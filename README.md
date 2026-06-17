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
Unlike basic script-based integrations that run once and exit, this bridge maintains a persistent SDK connection to Vector. This allows for lower latency, conversational memory, and reactive animations.

#### Recommended Wire-Pod Configuration:
1.  Open your Wire-Pod web interface (usually `http://localhost:8080`).
2.  Navigate to **Custom Intents**.
3.  Click **Add New Intent**.
4.  **Name**: `ollama_chat` (or any descriptive name).
5.  **Utterances**: `let's chat, talk to me, I have a question, chat with me, let's talk`.
6.  **Intent to send to robot**: Select `knowledge_question` or `imperative_praise`.
    - *Note: Using `imperative_praise` often results in a more neutral animation from Vector before he starts thinking.*
7.  **Action**: Set to **None**.
    - *Why? Our bridge script listens for the standard SDK intent triggered by Wire-Pod. Setting an Action in Wire-Pod might conflict with the SDK control.*

8.  **SDK Setup**: Ensure your robot is configured for the SDK:
    ```bash
    python3 -m anki_vector.configure
    ```

### Direct Connection (Headless/CLI Setup)
If you are running in a headless environment or using a CLI agent (like Gemini), you can bypass the interactive `anki_vector.configure` tool by providing connection details directly in your `.env` file.

1.  Gather your Vector's connection details: IP, Name (Vector-XXXX), Serial, GUID, and Certificate Path.
2.  Use the helper script to set up your environment:
    ```bash
    python3 src/utils/configure_env.py <IP> <NAME> <SERIAL> <GUID> <CERT_PATH>
    ```
    *Alternatively, you can manually edit the `.env` file and fill in the `VECTOR_` variables.*

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
