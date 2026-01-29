import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Optional, Any, List, Dict


class BaseSkill(ABC):
    """
    Ultimate Abstract Base Class for Assistant Skills (Plugins).

    This class implements the 'Template Method' design pattern. It provides a
    standardized execution lifecycle including validation, timeout protection,
    error handling, and metrics logging.

    Features:
        - 🛡️ **Safety Wrapper:** Prevents crashes via input validation & timeouts.
        - 🪝 **Lifecycle Hooks:** on_start, on_finish, on_error for customization.
        - 💾 **Persistence:** Easy-to-use helpers for context memory.
        - 📊 **Metrics:** Automatically tracks execution time and usage count.
    """

    # -------------------------
    # 🔹 Metadata (Override in child classes)
    # -------------------------
    name: str = "BaseSkill"
    keywords: List[str] = []
    description: str = "Base abstract skill."
    timeout: int = 15  # Default max execution time in seconds

    def __init__(self, data_manager: Optional[Any] = None):
        """
        Initialize skill with dependency injection.

        Args:
            data_manager: Shared instance for File I/O and Persistence.
        """
        self.data_manager = data_manager
        self.logger = logging.getLogger(f"Skill.{self.name}")
        self.execution_count = 0

    # -------------------------
    # 🛡️ Safety Execution Wrapper (The Brain calls this)
    # -------------------------
    async def run(self, args: str, timeout: Optional[int] = None) -> str:
        """
        The master controller method. It orchestrates the execution flow:
        Validation -> Config Check -> Hooks -> Execution -> Logging.
        """
        # 1. Input Validation
        if not self.validate_input(args):
            return self.format_error("Input is empty or invalid.")

        # 2. Configuration Check
        if not self.check_configuration():
            return self.format_error("Configuration check failed (Missing API Keys or Setup).")

        actual_timeout = timeout or self.timeout
        start_time = time.perf_counter()

        # 3. Execution Lifecycle
        try:
            # Hook: Pre-execution
            await self._safe_hook(self.on_start, args)

            self.logger.info(f"🚀 Running '{self.name}' with args: '{args}'")

            # CORE EXECUTION (With Timeout)
            result = await asyncio.wait_for(self.execute(args), timeout=actual_timeout)

            # Hook: Post-execution
            await self._safe_hook(self.on_finish, args, result)

            # Metrics
            self.execution_count += 1
            exec_time = time.perf_counter() - start_time
            self.logger.info(f"✅ '{self.name}' finished in {exec_time:.4f}s")

            # Note: We do NOT save history here.
            # The 'Brain' class handles conversation history to avoid duplicates.

            return result

        except asyncio.TimeoutError:
            msg = f"⏱️ Timeout: '{self.name}' exceeded {actual_timeout}s limit."
            self.logger.error(msg)
            await self._safe_hook(self.on_error, args, TimeoutError(msg))
            return self.format_error(msg)

        except Exception as e:
            self.logger.error(f"💥 Execution failure in '{self.name}': {e}", exc_info=True)
            await self._safe_hook(self.on_error, args, e)
            return self.format_error(f"An unexpected error occurred: {str(e)}")

    async def _safe_hook(self, hook, *args):
        """Helper to run lifecycle hooks without crashing the main process."""
        try:
            if asyncio.iscoroutinefunction(hook):
                await hook(*args)
        except Exception as e:
            self.logger.warning(f"⚠️ Hook '{hook.__name__}' failed: {e}")

    # -------------------------
    # 🧩 Abstract Core Logic (Must Override)
    # -------------------------
    @abstractmethod
    async def execute(self, args: str) -> str:
        """
        Core logic of the skill. Must be implemented as asynchronous.

        Args:
            args (str): User input.
        Returns:
            str: Response text (Markdown supported).
        """
        pass

    # -------------------------
    # 🪝 Lifecycle Hooks (Optional Override)
    # -------------------------
    async def on_start(self, args: str):
        """Hook called before execution starts."""
        pass

    async def on_finish(self, args: str, result: str):
        """Hook called after successful execution."""
        pass

    async def on_error(self, args: str, error: Exception):
        """Hook called when an exception occurs."""
        pass

    # -------------------------
    # 💾 Memory Utilities
    # -------------------------
    def save_to_memory(self, key: str, value: Any):
        """Persist key-value data to context memory safely."""
        if self.data_manager:
            try:
                self.data_manager.context_memory[key] = value
                self.data_manager.save_context()
                self.logger.debug(f"Memory saved: {key}")
            except Exception as e:
                self.logger.error(f"Failed to save memory '{key}': {e}")
        else:
            self.logger.warning("DataManager missing. Memory not saved.")

    def read_from_memory(self, key: str, default: Any = None) -> Any:
        """Read value from context memory."""
        if self.data_manager:
            return self.data_manager.context_memory.get(key, default)
        return default

    def safe_read_list(self, key: str) -> List[Any]:
        """Safely returns a list from memory."""
        val = self.read_from_memory(key)
        return val if isinstance(val, list) else []

    def safe_read_dict(self, key: str) -> Dict[str, Any]:
        """Safely returns a dict from memory."""
        val = self.read_from_memory(key)
        return val if isinstance(val, dict) else {}

    # -------------------------
    # 🔑 API & Validation Helpers
    # -------------------------
    def get_api_key(self, service_name: str) -> Optional[str]:
        """Securely fetch API key from DataManager."""
        if not self.data_manager:
            self.logger.warning(f"DataManager missing. Cannot fetch API key for {service_name}.")
            return None

        key = self.data_manager.get_api_key(service_name)
        if not key:
            self.logger.warning(f"API key for '{service_name}' not found in environment.")
        return key

    def validate_input(self, args: str) -> bool:
        """Basic validation: Checks if input is empty."""
        is_valid = bool(args and args.strip())
        if not is_valid:
            self.logger.warning("Validation failed: Empty input.")
        return is_valid

    def check_configuration(self) -> bool:
        """
        Override this to check if requirements (API keys, files) are met.
        Returns True by default.
        """
        return True

    def format_error(self, message: str) -> str:
        """Standardizes error UI output."""
        return f"❌ **{self.name.capitalize()} Error:** {message}"

    def __repr__(self):
        """Debug representation of the skill."""
        return f"<{self.__class__.__name__} name='{self.name}' executed={self.execution_count}>"