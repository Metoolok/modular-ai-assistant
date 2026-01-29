import asyncio
import logging
import importlib
import pkgutil
from pathlib import Path
from typing import Dict, Any, Optional

# Optional: NLP Library (Uncomment if needed for advanced Intent Recognition)
# import spacy

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class AssistantBrain:
    """
    The Central Intelligence Engine of the Assistant.

    Responsibilities:
    1. Dynamic Plugin Loading: Auto-discovers skills from the 'skills' folder.
    2. Intent Classification: Routes user input to the correct skill based on keywords.
    3. Memory Management: Orchestrates the flow of data between skills and long-term memory.
    4. Async Execution: Manages non-blocking operations for a smooth UI experience.
    """

    def __init__(self, data_manager, skill_folder="skills"):
        self.data_manager = data_manager
        self.context_memory = self.data_manager.context_memory

        # 1. Load Skills Dynamically (Dependency Injection happens here)
        self.skill_objects = self.load_skills(skill_folder)

        # 2. Build Intent Map automatically from loaded skills
        self.intent_map = self._build_intent_map()

        # self.nlp = spacy.load("en_core_web_sm") # Placeholder for future NLP logic

    # -------------------
    # 🔌 Dynamic System Loading
    # -------------------
    def load_skills(self, folder: str) -> Dict[str, Any]:
        """
        Scans the 'skills' directory, imports modules, and instantiates valid Skill classes.
        Injects 'data_manager' into each skill during instantiation.
        """
        skills = {}
        folder_path = Path(folder)

        if not folder_path.exists():
            logging.error(f"Skill folder '{folder}' not found.")
            return {}

        # Iterate over all modules in the skills package
        for _, name, _ in pkgutil.iter_modules([str(folder_path)]):
            try:
                module = importlib.import_module(f"{folder}.{name}")
                # Inspect module attributes to find Skill classes
                for attr in dir(module):
                    cls = getattr(module, attr)

                    # Check if it's a valid Skill class (inherits structure but isn't BaseSkill itself)
                    if isinstance(cls, type) and hasattr(cls, "execute") and hasattr(cls, "keywords"):
                        if cls.__name__ != "BaseSkill":
                            # CRITICAL: Inject DataManager here!
                            skill_instance = cls(self.data_manager)

                            # Use skill name as key (lowercase)
                            skill_name = getattr(skill_instance, "name", name).lower()
                            skills[skill_name] = skill_instance

            except Exception as e:
                logging.error(f"Failed to load module {name}: {e}")

        logging.info(f"System initialized with {len(skills)} skills: {list(skills.keys())}")
        return skills

    def _build_intent_map(self) -> Dict[str, list]:
        """
        Constructs the intent map by asking each skill for its keywords.
        This enables 'Plug & Play' architecture - no hardcoded intents in Brain.
        """
        intent_map = {}
        for name, skill in self.skill_objects.items():
            if hasattr(skill, 'keywords'):
                intent_map[name] = skill.keywords
        return intent_map

    # -------------------
    # 🧠 Core Processing Logic
    # -------------------
    async def process_input(self, text: str) -> str:
        """
        Main entry point for user queries.

        Args:
            text (str): The raw input from the user.
        Returns:
            str: The final response from the assistant.
        """
        text_lower = text.lower()
        logging.info(f"User Input: {text}")

        # 1. Detect Intent
        intent = self.detect_intent(text_lower)

        if not intent:
            available_skills = ", ".join([s.capitalize() for s in self.skill_objects.keys()])
            return f"🤔 I didn't understand that. I can currently help with: **{available_skills}**"

        skill = self.skill_objects.get(intent)

        if not skill:
            return f"❌ System Error: Intent '{intent}' detected, but module is not loaded."

        # 2. Route & Execute
        return await self.route_to_skill(skill, text)

    def detect_intent(self, text: str) -> Optional[str]:
        """Matches user text against the auto-generated keyword map."""
        for skill_name, keywords in self.intent_map.items():
            if any(kw in text for kw in keywords):
                return skill_name
        return None

    async def route_to_skill(self, skill, args: str) -> str:
        """
        Executes the selected skill safely.
        Uses the 'run' wrapper if available (for timeouts/logging), otherwise falls back to 'execute'.
        """
        try:
            # OPTION A: Use the robust 'run' method (Recommended)
            if hasattr(skill, 'run'):
                result = await skill.run(args)

            # OPTION B: Fallback for older skills (Direct Execution)
            elif asyncio.iscoroutinefunction(skill.execute):
                result = await skill.execute(args)
            else:
                # Run synchronous blocking code in a separate thread
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, skill.execute, args)

            # 3. Update Memory (Short-term & Long-term)
            self._update_memory(skill.name, args, result)
            return result

        except Exception as e:
            logging.error(f"Runtime Error in Brain routing to {skill.name}: {e}", exc_info=True)
            return f"❌ An internal error occurred while processing via {skill.name}."

    def _update_memory(self, skill_name, user_input, result):
        """Updates conversation history and persists context."""
        self.context_memory["last_action"] = skill_name
        self.context_memory["last_result"] = result

        history = self.context_memory.get("conversation_history", [])
        history.append({"user": user_input, "assistant": result})

        # Keep only last 10 turns to save space
        self.context_memory["conversation_history"] = history[-10:]

        self.data_manager.save_context()