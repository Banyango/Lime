import wireup

import lime_ai.app.config as config
import lime_ai.app.writers.logger as logger_writer
import lime_ai.app.writers.writer as writer
from lime_ai import core, libs

container = wireup.create_async_container(
    injectables=[config, logger_writer, writer, core, libs],
)
