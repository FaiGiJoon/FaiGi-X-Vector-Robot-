# FaiGi-X-Vector-Robot: Vector 1.0 + Ollama Local AI Bridge

This project establishes a production-ready, highly resilient local AI bridge between an Anki/DDL Vector robot and a local Ollama LLM instance. By leveraging Wire-Pod's Custom Intents, Vector can intercept voice commands and respond using a local LLM while maintaining his unique robot persona.

## Core Features
- **Asynchronous Architecture**: Built with `aiohttp` to minimize latency between user speech and Vector's response.
- **Conversational Memory**: A sliding window buffer allows Vector to handle contextual follow-up questions naturally.
- **Strict TTS Compliance**: Automated sanitization ensures responses are perfectly formatted for Vector's voice engine.
- **Resilient Networking**: Includes pre-flight health checks, exponential backoff retries, and graceful fallback mechanisms.
- **Secure Configuration**: Uses environment variables to keep your network setup private.

## Repository Structure
```
├── config/             # Sample Wire-Pod JSON intent payloads
├── src/
│   ├── core/           # Main bridge logic and API abstraction
│   └── utils/          # Helper functions, logging, and config loaders
├── tests/              # Unit and integration tests
├── .env.example        # Template for configuration
├── requirements.txt    # Pinned dependencies
└── README.md
```

## Prerequisites
- **Anki Vector 1.0**: Setup with [Wire-Pod](https://github.com/kercre123/wire-pod).
- **Ollama**: Installed and running locally ([ollama.com](https://ollama.com/)).
- **Python 3.8+**: Recommended for optimal async performance.

## Setup Instructions

### 1. Configure Ollama
Pull your preferred model (default is `llama3`):
```bash
ollama pull llama3
```

### 2. Configure Environment
Copy the example environment file and fill in your details:
```bash
cp .env.example .env
```
Edit `.env` with your `OLLAMA_BASE_URL` and `WIRE_POD_IP`.

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Wire-Pod Integration
To use this bridge, configure a **Custom Intent** or **Knowledge Graph** in Wire-Pod:
1. Open your Wire-Pod web interface.
2. Navigate to **Behavior Settings** > **Knowledge Graph**.
3. Set the provider to "Custom" and point it to the IP/port where this script will be listening (if using a web-server wrapper) OR ensure Wire-Pod is configured to send `knowledge_question` intents to the SDK.
4. Example Utterances: "Talk to me", "I have a question", "Hey Vector, ask the AI...".

## Running the Bridge
Start the integration:
```bash
python src/core/vector_ollama.py
```

## Troubleshooting
- **Network Conflicts**: Ensure no firewalls are blocking communication between the Wire-Pod host and the Ollama server (default port `11434`).
- **Ollama Offline**: The script will perform a health check on startup. If it fails, verify Ollama is running by visiting `http://localhost:11434/api/tags` in your browser.
- **Robot Connection**: Ensure you have run `python3 -m anki_vector.configure` and the robot is on the same network.
- **Latency**: If responses are slow, try a smaller model like `tinyllama` or `phi3`.
