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
        "OLLAMA_API_KEY": os.getenv("OLLAMA_API_KEY", ""),
        "WIRE_POD_IP": os.getenv("WIRE_POD_IP", ""),
        "PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION": os.getenv("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python"),
        "VECTOR_IP": os.getenv("VECTOR_IP", ""),
        "VECTOR_NAME": os.getenv("VECTOR_NAME", ""),
        "VECTOR_SERIAL": os.getenv("VECTOR_SERIAL", ""),
        "VECTOR_GUID": os.getenv("VECTOR_GUID", ""),
        "VECTOR_CERT_PATH": os.getenv("VECTOR_CERT_PATH", "")
    }

    # Set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION for the current process
    os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = config["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"]

    return config
