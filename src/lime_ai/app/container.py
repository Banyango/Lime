import wireup

import lime_ai.app.cli.writers.logger as logger_writer
import lime_ai.app.cli.writers.writer as writer
import lime_ai.app.config as config
from lime_ai import core, libs

container = wireup.create_async_container(
    injectables=[config, logger_writer, writer, core, libs],
)
