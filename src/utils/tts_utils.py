import re

def sanitize_for_tts(text):
    """
    Enforces strict TTS compliance by removing prohibited characters and enforcing length caps.

    Rules:
    - Max 2 sentences.
    - Max 35 words.
    - Raw alphanumeric text only.
    - No markdown, asterisks, brackets, emojis, etc.
    - Spell out numbers 0-9.
    """
    # Remove markdown characters explicitly before general filtering
    text = re.sub(r'[*_`#]', '', text)

    # Basic number to word conversion for digits 0-9
    num_map = {
        '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
        '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'
    }

    # Replace digits with words
    text = "".join(num_map.get(c, c) for c in text)

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
