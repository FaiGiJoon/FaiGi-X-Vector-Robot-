import os
from dotenv import load_dotenv

def load_config():
    """
    Loads environment variables from .env file.
    """
    load_dotenv()

    config = {
        "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "OLLAMA_MODEL": os.getenv("OLLAMA_MODEL", "llama3"),
        "WIRE_POD_IP": os.getenv("WIRE_POD_IP", ""),
        "PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION": os.getenv("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")
    }

    # Set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION for the current process
    os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = config["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"]

    return config
