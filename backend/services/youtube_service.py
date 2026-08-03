import os
import yt_dlp

FFMPEG_BIN_DIR = r"C:\ffmpeg-8.1.2-essentials_build\bin"


def _ffmpeg_location():
    """Only pass ffmpeg_location if that hardcoded Windows path actually exists,
    otherwise let yt-dlp find ffmpeg on PATH (e.g. on Mac/Linux)."""
    return FFMPEG_BIN_DIR if os.path.isdir(FFMPEG_BIN_DIR) else None


def extract_video_id(youtube_url):

    if "youtu.be/" in youtube_url:
        return youtube_url.split("youtu.be/")[1].split("?")[0]

    elif "watch?v=" in youtube_url:
        return youtube_url.split("watch?v=")[1].split("&")[0]

    return None


def download_audio(video_url):
    """Downloads just the audio -> used for Whisper transcription."""

    os.makedirs("downloads", exist_ok=True)

    output_path = "downloads/audio"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "quiet": False,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    loc = _ffmpeg_location()
    if loc:
        ydl_opts["ffmpeg_location"] = loc

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    return "downloads/audio.mp3"


def download_video(video_url):
    """Downloads the actual video (video+audio muxed as mp4) so we have
    something to cut clips FROM later with ffmpeg. Audio-only download
    isn't enough once we get to the clipping step."""

    os.makedirs("downloads", exist_ok=True)

    output_path = "downloads/video"

    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": output_path + ".%(ext)s",
        "quiet": False,
        "noplaylist": True,
        "merge_output_format": "mp4",
    }

    loc = _ffmpeg_location()
    if loc:
        ydl_opts["ffmpeg_location"] = loc

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    return output_path + ".mp4"
