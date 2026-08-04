from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from services.youtube_service import extract_video_id, download_audio, download_video
from services.transcript_service import get_transcript
from services.gemini_service import detect_speakers, get_speaker_timestamps
from services.clip_service import cut_clips

app = Flask(__name__)
CORS(app)

# Simple in-memory cache so we don't have to re-download / re-transcribe
# the video every time the frontend asks for timestamps or clips.
# Keyed by video_id -> {"video_path": ..., "segments": [...]}
VIDEO_CACHE = {}


@app.route("/")
def home():
    return "FocusClip AI Backend Running 🚀"


@app.route("/analyze", methods=["POST"])
def analyze():

    try:

        data = request.get_json()
        youtube_url = data.get("youtube_url")

        if not youtube_url:
            return jsonify({"status": "error", "message": "No YouTube URL provided"})

        video_id = extract_video_id(youtube_url)
        if not video_id:
            return jsonify({"status": "error", "message": "Could not read a video ID from that URL"})

        print("STEP 1 - Downloading audio...")
        audio_path = download_audio(youtube_url)

        print("STEP 2 - Downloading video (needed later for clipping)...")
        video_path = download_video(youtube_url)

        print("STEP 3 - Running Whisper...")
        transcript, segments = get_transcript(audio_path)

        print("STEP 4 - Transcript length:", len(transcript))

        print("STEP 5 - Detecting speakers...")
        speakers = detect_speakers(transcript)

        print("STEP 6 - Speakers:", speakers)

        VIDEO_CACHE[video_id] = {
            "video_path": video_path,
            "segments": segments,
        }

        return jsonify({
            "status": "success",
            "youtube_url": youtube_url,
            "video_id": video_id,
            "transcript": transcript[:1000],
            "speakers": speakers
        })

    except Exception as e:
        import traceback
        traceback.print_exc()

        return jsonify({
            "status": "error",
            "message": str(e)
        })


@app.route("/speaker-timestamps", methods=["POST"])
def speaker_timestamps():
    """Given a video_id (already analyzed) and a speaker name, ask Gemini
    which moments in the transcript that speaker was talking."""

    try:
        data = request.get_json()
        video_id = data.get("video_id")
        speaker = data.get("speaker")
        topic = data.get("topic")

        if not video_id or video_id not in VIDEO_CACHE:
            return jsonify({
                "status": "error",
                "message": "No cached data for this video. Please analyze it again."
            })

        if not speaker:
            return jsonify({"status": "error", "message": "No speaker provided"})

        segments = VIDEO_CACHE[video_id]["segments"]

        if topic:
            print(f"STEP - Finding moments where {speaker} talks about \"{topic}\"...")
        else:
            print(f"STEP - Finding timestamps for {speaker}...")

        timestamps = get_speaker_timestamps(segments, speaker, topic=topic)
        print(f"STEP - Found {len(timestamps)} range(s) for {speaker}")

        return jsonify({
            "status": "success",
            "speaker": speaker,
            "topic": topic,
            "timestamps": timestamps
        })

    except Exception as e:
        import traceback
        traceback.print_exc()

        return jsonify({"status": "error", "message": str(e)})


@app.route("/generate-clips", methods=["POST"])
def generate_clips():
    """Given a video_id, speaker, and their timestamp ranges, cut real
    .mp4 clips with ffmpeg and return download URLs for each."""

    try:
        data = request.get_json()
        video_id = data.get("video_id")
        speaker = data.get("speaker")
        timestamps = data.get("timestamps")

        if not video_id or video_id not in VIDEO_CACHE:
            return jsonify({
                "status": "error",
                "message": "No cached data for this video. Please analyze it again."
            })

        if not timestamps:
            return jsonify({"status": "error", "message": "No timestamps provided"})

        video_path = VIDEO_CACHE[video_id]["video_path"]

        print(f"STEP - Cutting {len(timestamps)} clip(s) for {speaker}...")
        clip_paths = cut_clips(video_path, timestamps, video_id, speaker)

        if not clip_paths:
            return jsonify({
                "status": "error",
                "message": "ffmpeg couldn't produce any clips. Check the backend logs."
            })

        clip_urls = ["/clips/" + p.split("clips/", 1)[1] for p in clip_paths]

        return jsonify({
            "status": "success",
            "speaker": speaker,
            "clips": clip_urls
        })

    except Exception as e:
        import traceback
        traceback.print_exc()

        return jsonify({"status": "error", "message": str(e)})


@app.route("/clips/<path:filepath>")
def serve_clip(filepath):
    return send_from_directory("clips", filepath)


if __name__ == "__main__":
    app.run(debug=True)
