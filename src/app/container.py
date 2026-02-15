import wireup

import app.writers.writer as writer
import app.config as config
import core
import libs


container = wireup.create_async_container(
    injectables=[config, writer, core, libs],
)
