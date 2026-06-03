import re

def sanitize_for_tts(text):
    """
    Enforces strict TTS compliance by removing prohibited characters and enforcing length caps.

    Rules:
    - Max 2 sentences.
    - Max 35 words.
    - Raw alphanumeric text only.
    - No markdown, asterisks, brackets, emojis, etc.
    """
    # Remove characters that aren't alphanumeric, space, basic punctuation, or apostrophes
    sanitized = "".join(c for c in text if c.isalnum() or c in " ,.!?\'")

    # Enforce sentence cap (max 2)
    sentences = re.split(r'(?<=[.!?])\s+', sanitized.strip())
    if len(sentences) > 2:
        sanitized = " ".join(sentences[:2])
    else:
        sanitized = " ".join(sentences)

    # Enforce word cap (max 35 words)
    words = sanitized.split()
    if len(words) > 35:
        sanitized = " ".join(words[:35])

    return sanitized.strip()
