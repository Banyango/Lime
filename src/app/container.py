import wireup

import app.config as config
import app.writers.logger as logger_writer
import app.writers.writer as writer
import core
import libs

container = wireup.create_async_container(
    injectables=[config, logger_writer, writer, core, libs],
)
