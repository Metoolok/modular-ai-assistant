import os
import uuid
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()


class DataManager:
    """
    Manages File I/O, API security, and persistent context storage (Long-term memory).
    Designed to be thread-safe and robust against missing files.
    """

    def __init__(self, temp_folder: str = "temp", context_file: str = "context.json"):
        self.temp_folder = Path(temp_folder)
        self.temp_folder.mkdir(parents=True, exist_ok=True)
        self.context_file = Path(context_file)
        self.context_memory = self.load_context()

    def upload_file(self, file) -> Optional[str]:
        """
        Saves an uploaded file securely with a unique identifier (UUID) to prevent overwrites.

        Args:
            file: The file object from Streamlit or API.
        Returns:
            str: Absolute path of the saved file, or None on failure.
        """
        if not file:
            return None

        # Generate unique name: 'a1b2c3d4_filename.pdf'
        unique_name = f"{uuid.uuid4().hex[:8]}_{file.name}"
        file_path = self.temp_folder / unique_name

        try:
            file_path.write_bytes(file.getbuffer())
            logging.info(f"File saved successfully: {file_path}")
            return str(file_path)
        except Exception as e:
            logging.error(f"Error saving file: {e}")
            return None

    def get_api_key(self, service_name: str) -> Optional[str]:
        """Retrieves API keys from environment variables for security."""
        key = os.getenv(f"{service_name.upper()}_API_KEY")
        if not key:
            logging.warning(f"API Key for {service_name} is missing in .env")
        return key

    def delete_file(self, file_path: str) -> bool:
        """Removes a temporary file from the system."""
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
        return False

    # -------------------
    # Persistent Memory (JSON Database)
    # -------------------
    def load_context(self) -> Dict[str, Any]:
        """Loads the conversation context from a JSON file."""
        if self.context_file.exists():
            try:
                with open(self.context_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logging.error("Context file is corrupted. Starting with empty memory.")
                return {}
        return {}

    def save_context(self):
        """Saves current memory state to JSON file."""
        try:
            with open(self.context_file, "w", encoding="utf-8") as f:
                json.dump(self.context_memory, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Failed to save context: {e}")