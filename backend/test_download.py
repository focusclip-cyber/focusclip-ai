from services.youtube_service import download_audio

url = "https://www.youtube.com/watch?v=Hh6kD4hg0Ic"

audio = download_audio(url)

print(audio)