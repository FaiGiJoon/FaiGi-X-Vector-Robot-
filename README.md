# FaiGi-X-Vector-Robot: Vector 1.0 + Ollama Local AI Bridge

This project establishes a production-ready, highly resilient local AI bridge between an Anki/DDL Vector robot and a local Ollama LLM instance. By leveraging Wire-Pod's Custom Intents, Vector can intercept voice commands and respond using a local LLM while maintaining his unique robot persona.

## Core Features
- **Asynchronous Architecture**: Built with a background event loop to minimize latency between user speech and Vector's response.
- **Dynamic Persona**: Integrated telemetry allows Vector's personality to react to his physical state (e.g., battery levels).
- **Conversational Memory**: A sliding window buffer allows Vector to handle contextual follow-up questions naturally.
- **Strict TTS Compliance**: Automated sanitization with unit expansion (e.g., "V" to "volts") ensures natural, perfectly formatted speech.
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

**Advanced: Optimized Vector Model**
This repository includes a `Modelfile` to create a dedicated 'vector' model with an optimized system prompt and parameters:
```bash
ollama create vector -f Modelfile
```
Then update your `.env` to use `OLLAMA_MODEL=vector`.

### 2. Configure Environment
Copy the example environment file and fill in your details:
```bash
cp .env.example .env
```
Edit `.env` with your `OLLAMA_BASE_URL` and `WIRE_POD_IP`.

**Important Note on Protobuf:**
If you encounter `TypeError: Descriptors cannot be created directly` when running the script, you must set an environment variable to use the pure-Python implementation of Protobuf:
```bash
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
```
This project handles this automatically if set in your `.env` file.

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Wire-Pod Integration
To use this bridge, configure a **Custom Intent** in Wire-Pod:
1. Open your Wire-Pod web interface (usually `http://<wire-pod-ip>:8080`).
2. Navigate to **Custom Intents**.
3. Click **Add New Intent**.
4. **Name**: `knowledge_question` or any name you prefer.
5. **Utterances**: Add phrases like "Talk to me", "I have a question", "Hey Vector, ask the AI".
6. **Action**: Set to `Script` or `Web-hook` depending on how you've set up your bridge.
7. Ensure your robot is connected to the SDK: `python3 -m anki_vector.configure`.

## Running the Bridge
Start the integration:
```bash
python src/core/vector_ollama.py
```

## Developer Guide

### Running Tests
The project includes a suite of integration tests to verify the LLM bridge and TTS sanitization logic.
```bash
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
python3 tests/test_integration.py
```

### Code Style
- **Asynchronous**: Use `async`/`await` for all I/O operations.
- **Persona**: Maintain the "Vector 1.0" persona—precise, analytical, and slightly sarcastic.
- **TTS**: Always pass LLM output through `sanitize_for_tts` before sending it to the robot.

## Troubleshooting
- **Network Conflicts**: Ensure no firewalls are blocking communication between the Wire-Pod host and the Ollama server (default port `11434`).
- **Ollama Offline**: The script will perform a health check on startup. If it fails, verify Ollama is running.
- **Robot Connection**: Ensure you have run `python3 -m anki_vector.configure` and the robot is on the same network.
- **Latency**: If responses are slow, try a smaller model like `tinyllama` or `phi3`.
