import datetime
from .base import BaseSkill


class TodoSkill(BaseSkill):
    """
    Manages a persistent To-Do list with CRUD operations.
    Demonstrates: JSON Persistence, List manipulation, Metadata handling.
    """
    name = "todo"
    keywords = ["task", "görev", "todo", "list", "hatırlat", "yapılacak", "add", "ekle"]
    description = "Manages your daily tasks."

    async def execute(self, args: str) -> str:
        # Load tasks safely
        context = self.data_manager.context_memory if self.data_manager else {}
        tasks = context.get("todo_list", [])

        try:
            # ADD TASK
            if "add:" in args or "ekle" in args:
                splitter = "add:" if "add:" in args else "ekle"
                try:
                    task_content = args.split(splitter, 1)[1].strip()
                except IndexError:
                    return "⚠️ Please write the task. Example: `todo add: Buy milk`"

                if not task_content: return "⚠️ Cannot add an empty task."

                new_task = {
                    "task": task_content,
                    "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "status": "pending"
                }
                tasks.append(new_task)

                # Save
                self._save_tasks(context, tasks)
                return f"✅ **Task Added:** {task_content}"

            # LIST TASKS
            elif "list" in args or "göster" in args:
                if not tasks: return "📂 Your to-do list is empty."

                formatted = []
                for i, t in enumerate(tasks):
                    # Backward compatibility check for old data
                    task_text = t.get('task', t) if isinstance(t, dict) else t
                    time_text = f" _({t.get('created_at', '')})_" if isinstance(t, dict) else ""
                    formatted.append(f"{i + 1}. {task_text}{time_text}")

                return "### 📝 Your Tasks\n" + "\n".join(formatted)

            # CLEAR LIST
            elif "clear" in args or "temizle" in args:
                self._save_tasks(context, [])
                return "🗑️ List cleared."

            return "💡 **Usage:** `todo add: Buy milk`, `todo list`, `todo clear`"

        except Exception as e:
            return f"❌ Todo Error: {str(e)}"

    def _save_tasks(self, context, tasks):
        """Helper to safely save tasks to persistent storage."""
        context["todo_list"] = tasks
        if self.data_manager:
            self.data_manager.save_context()