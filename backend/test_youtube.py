from services.youtube_service import extract_video_id

url = "https://youtu.be/Hh6kD4hg0Ic"

video_id = extract_video_id(url)

print(video_id)