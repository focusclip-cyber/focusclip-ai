from services.youtube_service import extract_video_id
from services.transcript_service import get_transcript
from services.gemini_service import detect_speakers

url = "https://youtu.be/Hh6kD4hg0Ic"

video_id = extract_video_id(url)

print("Video ID:", video_id)

transcript = get_transcript(video_id)

print("\nTranscript:")
print(transcript)

speakers = detect_speakers(transcript)

print("\nDetected Speakers:")
print(speakers)