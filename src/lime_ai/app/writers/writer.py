from typing import Any

from rich.text import Text
from wireup import injectable

from lime_ai.app.config import AppConfig
from lime_ai.app.display.app import LimeApp
from lime_ai.core.agents.models import ExecutionModel
from lime_ai.core.interfaces.ui import UI


@injectable(as_type=UI)
class CliWriter(UI):
    def __init__(self, app_config: AppConfig):
        self.app_config = app_config
        self._tool_call_cache: dict[str, Any] = {}

    async def render_ui(self, execution_model: ExecutionModel):
        app = LimeApp(execution_model=execution_model, app_config=self.app_config)
        await app.run_async()
