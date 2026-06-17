import re

def number_to_words(n):
    """
    Simple converter for numbers to words (0-99).
    """
    units = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    teens = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

    if 0 <= n < 10:
        return units[n]
    elif 10 <= n < 20:
        return teens[n-10]
    elif 20 <= n < 100:
        return tens[n//10] + ((" " + units[n%10]) if (n % 10 != 0) else "")
    else:
        # Fallback for larger numbers: spell out digits
        return " ".join(units[int(d)] for d in str(n))

def sanitize_for_tts(text):
    """
    Enforces strict TTS compliance by removing prohibited characters and enforcing length caps.

    Rules:
    - Max 2 sentences.
    - Max 35 words.
    - Raw alphanumeric text only.
    - No markdown, asterisks, brackets, emojis, etc.
    - Spell out numbers 0-99.
    """
    # Replace dashes and underscores with spaces to avoid merging words
    text = text.replace("-", " ").replace("_", " ")

    # Remove markdown characters explicitly before general filtering
    text = re.sub(r'[*`#]', '', text)

    # Ensure space between numbers and units (e.g., "4V" -> "4 V")
    text = re.sub(r'(\d+)([a-zA-Z]+)', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z]+)(\d+)', r'\1 \2', text)

    # Expand common units and abbreviations for natural speech
    abbreviations = {
        r'\bV\b': 'volts',
        r'\bm\b': 'meters',
        r'\bcm\b': 'centimeters',
        r'\bkg\b': 'kilograms',
        r'\bC\b': 'Celsius',
        r'\bF\b': 'Fahrenheit',
        r'\bkm/h\b': 'kilometers per hour',
        r'\bmph\b': 'miles per hour',
        r'%': ' percent'
    }
    for pattern, replacement in abbreviations.items():
        text = re.sub(pattern, replacement, text)

    # Convert numbers to words (0-99)
    def replace_num(match):
        return number_to_words(int(match.group()))

    text = re.sub(r'\b\d{1,2}\b', replace_num, text)

    # For longer numbers, spell out each digit with spaces
    num_map = {
        '0': ' zero ', '1': ' one ', '2': ' two ', '3': ' three ', '4': ' four ',
        '5': ' five ', '6': ' six ', '7': ' seven ', '8': ' eight ', '9': ' nine '
    }
    text = "".join(num_map.get(c, c) for c in text)

    # Clean up multiple spaces that might have been introduced
    text = re.sub(r'\s+', ' ', text)

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
