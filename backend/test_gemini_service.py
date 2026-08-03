from services.gemini_service import detect_speakers

transcript = """
Becky: Welcome everyone.

Mary: Thank you Becky.

Becky: Today we will discuss AI.

John: Let's begin.
"""

speakers = detect_speakers(transcript)

print(speakers)