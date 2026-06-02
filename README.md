# Anki Vector 1.0 + Ollama Integration

This project provides a Python script to integrate Anki Vector 1.0 with an Ollama server, allowing Vector to answer questions using local Large Language Models (LLMs) like Llama 3.

## Prerequisites

1.  **Anki Vector 1.0 Robot**: Ensure your Vector is set up and accessible. (Works best with [WirePod](https://github.com/kercre123/wire-pod)).
2.  **Ollama**: Install Ollama from [ollama.com](https://ollama.com/).
3.  **Python 3.6+**: Ensure Python is installed on your machine.

## Setup Instructions

### 1. Install Ollama and Pull a Model

After installing Ollama, pull the model you wish to use (default is `llama3`):

```bash
ollama pull llama3
```

Ensure the Ollama server is running (it usually starts automatically).

### 2. Configure Vector SDK

If you haven't already, install the Vector SDK and configure your connection:

```bash
pip install anki_vector
python3 -m anki_vector.configure
```

Follow the prompts to enter your robot's name, IP address, serial number, and credentials.

### 3. Install Dependencies

Install the required Python libraries for this integration:

```bash
pip install -r requirements.txt
```

## Running the Integration

1.  Open `vector_ollama.py` and ensure the `OLLAMA_MODEL` variable matches the model you pulled (default is `llama3`).
2.  Run the script:

```bash
python3 vector_ollama.py
```

3.  Once the script says "Connected!", you can ask Vector a question.
    -   Say: **"Hey Vector, I have a question."**
    -   Vector will wait for your query. Ask your question (e.g., "Why is the sky blue?").
    -   Vector will send the query to Ollama and speak the response.

## Troubleshooting

-   **Connection Error**: Ensure Vector is on the same network and WirePod (if used) is running.
-   **Ollama Error**: Check if Ollama is running by visiting `http://localhost:11434` in your browser.
-   **Intent Data**: The script prints `intent_data` to the console. If Vector doesn't respond as expected, check the console output to see if the JSON structure of the voice command has changed.
