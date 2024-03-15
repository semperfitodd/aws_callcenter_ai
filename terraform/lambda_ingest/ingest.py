import json
import logging
import os
from datetime import datetime
from urllib.parse import unquote_plus

import boto3
from botocore.response import StreamingBody

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
transcribe_client = boto3.client('transcribe')
comprehend_client = boto3.client('comprehend')
dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client(service_name='bedrock-runtime')


def invoke_bedrock_model(full_text):
    body = json.dumps(
        {"prompt": f"\n\nHuman: Summarize this transcript. {full_text} \n\nAssistant:", "max_tokens_to_sample": 3000,
            "temperature": 0.5, "top_p": 1, })

    modelId = 'anthropic.claude-instant-v1'
    accept = 'application/json'
    contentType = 'application/json'

    response = bedrock.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)
    if isinstance(response.get('body'), StreamingBody):
        response_content = response['body'].read().decode('utf-8')
    else:
        response_content = response.get('body')
    response_body = json.loads(response_content)

    return response_body


def process_transcript(transcript, speaker_labels):
    dialogue_entries = []
    last_speaker = None

    for segment in speaker_labels['segments']:
        speaker_label = segment['speaker_label']
        speaker_name = {"spk_0": "Customer", "spk_1": "Agent"}[speaker_label]

        if last_speaker != speaker_label:
            if last_speaker is not None:
                dialogue_entries.append("\n")
            dialogue_entries.append(f"{speaker_name}:")
            last_speaker = speaker_label

        segment_dialogue = ""

        for item in segment['items']:
            word_info = next((word for word in transcript['items'] if
                              'start_time' in word and word['start_time'] == item['start_time']), None)
            if word_info and 'alternatives' in word_info and len(word_info['alternatives']) > 0:
                if segment_dialogue:
                    segment_dialogue += " "
                segment_dialogue += word_info['alternatives'][0]['content']

        if segment_dialogue:
            dialogue_entries.append(f" {segment_dialogue}")

    formatted_script = "".join(dialogue_entries)
    return formatted_script


def lambda_handler(event, context):
    DYNAMO_TABLE = os.environ['DYNAMO_TABLE']
    TRANSCRIBE_S3_BUCKET = os.environ['TRANSCRIBE_S3_BUCKET']

    for record in event['Records']:
        source_bucket_name = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])
        file_uri = f's3://{source_bucket_name}/{key}'

        transcribe_job_name = f"Transcription-{datetime.now().strftime('%Y%m%dT%H%M%S')}"
        transcribe_client.start_transcription_job(TranscriptionJobName=transcribe_job_name,
            Media={'MediaFileUri': file_uri}, MediaFormat='mp3', LanguageCode='en-US',
            OutputBucketName=TRANSCRIBE_S3_BUCKET, Settings={'ShowSpeakerLabels': True, 'MaxSpeakerLabels': 2})

        while True:
            status = transcribe_client.get_transcription_job(TranscriptionJobName=transcribe_job_name)
            if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
                break

        if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
            transcript_key = f"{transcribe_job_name}.json"
            transcript_response = s3_client.get_object(Bucket=TRANSCRIBE_S3_BUCKET, Key=transcript_key)
            transcript = json.loads(transcript_response['Body'].read().decode('utf-8'))
            full_text = process_transcript(transcript['results'], transcript['results']['speaker_labels'])

            summary_response = invoke_bedrock_model(full_text)
            summary = summary_response.get('completion', '')

            logger.info(summary)

            thirds = [full_text[i:i + len(full_text) // 3] for i in range(0, len(full_text), len(full_text) // 3)]
            sentiments = [comprehend_client.detect_sentiment(Text=part, LanguageCode='en')['Sentiment'] for part in
                          thirds]

            table = dynamodb.Table(DYNAMO_TABLE)
            table.put_item(Item={'UniqueId': key.split('.')[0], 'Date': datetime.now().strftime('%Y-%m-%d-%H-%M-%S'),
                'TranscriptionFull': full_text, 'Sentiment0': sentiments[0], 'Sentiment1': sentiments[1],
                'Sentiment2': sentiments[2], 'Summary': summary.strip()})
            return {'statusCode': 201, 'body': json.dumps('Success')}
        else:
            return {'statusCode': 500, 'body': json.dumps('Transcription job failed')}
