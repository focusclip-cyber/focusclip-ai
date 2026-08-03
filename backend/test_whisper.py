from services.transcript_service import get_transcript

transcript = get_transcript("downloads/audio.mp3")

print(transcript)