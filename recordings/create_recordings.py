import boto3
import glob
import os
from pydub import AudioSegment

polly_client = boto3.client('polly')


def synthesize_speech(text, voice_id, index):
    filename = f"segment_{index}.mp3"
    response = polly_client.synthesize_speech(
        Engine='long-form',
        Text=text,
        TextType='text',
        OutputFormat='mp3',
        VoiceId=voice_id
    )
    audio = response['AudioStream'].read()
    with open(filename, 'wb') as file:
        file.write(audio)
    return filename


def read_segments_from_file(filename):
    segments = []
    with open(filename, 'r') as file:
        for line in file:
            if ': ' in line:
                voice_id, text = line.split(': ', 1)
                segments.append((text.strip(), voice_id))
    return segments


for txt_file in glob.glob('*.txt'):
    segments = read_segments_from_file(txt_file)
    audio_files = [synthesize_speech(text, voice, index) for index, (text, voice) in enumerate(segments)]
    combined = AudioSegment.empty()
    for file_name in audio_files:
        segment = AudioSegment.from_mp3(file_name)
        combined += segment
    mp3_filename = f"{os.path.splitext(txt_file)[0]}.mp3"
    combined.export(mp3_filename, format="mp3")
    for file_name in audio_files:
        os.remove(file_name)
    print(f"Combined audio created: {mp3_filename}")
