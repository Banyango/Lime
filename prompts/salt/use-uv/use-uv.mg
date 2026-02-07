<<
Project should use uv for dependency management.

pyproject.toml:
```toml
[build-system]
requires = ["uv"]
build-backend = "uv.build"
```
>>