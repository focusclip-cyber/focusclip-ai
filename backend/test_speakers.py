from services.transcript_service import get_transcript
from services.gemini_service import detect_speakers

transcript = get_transcript("downloads/audio.mp3")

print("Transcript loaded...\n")

speakers = detect_speakers(transcript)

print("Detected Speakers:\n")
print(speakers)