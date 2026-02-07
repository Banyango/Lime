import wireup

import app.writers.writer as writer
import core
import libs


container = wireup.create_async_container(
    injectables=[writer, core, libs],
)
