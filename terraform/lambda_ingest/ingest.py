import base64
import json
import logging
import os
from datetime import datetime
from urllib.parse import unquote_plus

import boto3
import requests
from botocore.response import StreamingBody

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
transcribe_client = boto3.client('transcribe')
comprehend_client = boto3.client('comprehend')
dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client(service_name='bedrock-runtime')

SLACK_SECRET_NAME = os.environ['SLACK_SECRET_NAME']


def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    if 'SecretString' in response:
        secret = json.loads(response['SecretString'])
        return secret['webhook_url']
    else:
        decoded_binary_secret = base64.b64decode(response['SecretBinary'])
        return decoded_binary_secret


def invoke_bedrock_model(full_text):
    payload = {
        "prompt": f"\n\nHuman: Summarize this transcript. {full_text} \n\nAssistant:",
        "max_tokens_to_sample": 3000,
        "temperature": 0.5,
        "top_p": 1,
    }
    model_id = 'anthropic.claude-instant-v1'
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    response = bedrock.invoke_model(body=json.dumps(payload), modelId=model_id, accept=headers['Accept'], contentType=headers['Content-Type'])
    if isinstance(response.get('body'), StreamingBody):
        response_content = response['body'].read().decode('utf-8')
    else:
        response_content = response.get('body')
    return json.loads(response_content)


def process_transcript(transcript, speaker_labels):
    dialogue_entries = []
    last_speaker = None

    for segment in speaker_labels['segments']:
        speaker_label = segment['speaker_label']
        speaker_name = {"spk_0": "Customer", "spk_1": "Agent"}.get(speaker_label, "Unknown")

        if last_speaker != speaker_label:
            dialogue_entries.append("\n" if last_speaker is not None else "")
            dialogue_entries.append(f"{speaker_name}:")
            last_speaker = speaker_label

        segment_dialogue = " ".join(
            word['alternatives'][0]['content']
            for item in segment['items']
            if (word := next((word for word in transcript['items'] if 'start_time' in word and word['start_time'] == item['start_time']), None))
            and 'alternatives' in word and word['alternatives']
        )

        if segment_dialogue:
            dialogue_entries.append(f" {segment_dialogue}")

    return "".join(dialogue_entries)


def send_slack_message(webhook_url, message):
    headers = {'Content-type': 'application/json'}
    payload = {"text": message}
    response = requests.post(webhook_url, json=payload, headers=headers)
    if response.status_code != 200:
        logger.error(f"Failed to send message to Slack: {response.text}")


def lambda_handler(event, context):
    DYNAMO_TABLE = os.environ['DYNAMO_TABLE']
    TRANSCRIBE_S3_BUCKET = os.environ['TRANSCRIBE_S3_BUCKET']
    slack_webhook_url = get_secret(SLACK_SECRET_NAME)

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

            if sentiments[2] != 'POSITIVE':
                slack_message = f"Final Sentiment: {sentiments[2]}, UniqueID: {key.split('.')[0]}"
                send_slack_message(slack_webhook_url, slack_message)

            table = dynamodb.Table(DYNAMO_TABLE)
            table.put_item(Item={
                'UniqueId': key.split('.')[0],
                'Date': datetime.now().strftime('%Y-%m-%d-%H-%M-%S'),
                'TranscriptionFull': full_text,
                'Sentiment0': sentiments[0],
                'Sentiment1': sentiments[1],
                'Sentiment2': sentiments[2],
                'Summary': summary.strip()
            })
            return {'statusCode': 201, 'body': json.dumps('Success')}
        else:
            return {'statusCode': 500, 'body': json.dumps('Transcription job failed')}
