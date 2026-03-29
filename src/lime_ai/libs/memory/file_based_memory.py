import json
from pathlib import Path

from wireup import injectable

from lime_ai.core.agents.services.memory import MemoryService
from lime_ai.entities.context import Context
from lime_ai.entities.memory import Memory


@injectable(as_type=MemoryService)
class FileBasedMemoryService(MemoryService):
    async def save_memory(self, memory: Memory):
        current_dir = Path.cwd()
        memory_path = Path(current_dir / "memory.json")
        memory_path.parent.mkdir(parents=True, exist_ok=True)

        memory_path.write_text(json.dumps(memory.get_all(), indent=2, sort_keys=True) + "\n")

    async def load_memory(self, context: Context):
        current_dir = Path.cwd()
        memory = Memory(context)

        memory_path = Path(current_dir / "memory.json")

        if memory_path.is_file():
            try:
                data = json.loads(memory_path.read_text())
                for key, value in data.items():
                    memory.set(key, value)
            except (json.JSONDecodeError, ValueError):
                pass

        return memory
