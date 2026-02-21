from abc import ABC, abstractmethod
from pathlib import Path

from entities.prompt_integrity import PromptLock


class PromptIntegrity(ABC):
    @abstractmethod
    def load_policy(self, manifest_path: Path, lock_path: Path):
        """Load and validate prompt integrity policy files."""

    @abstractmethod
    def verify_trusted_path(self, path: Path):
        """Verify that a path is inside the trusted prompt root."""

    @abstractmethod
    def verify_bytes(self, path: Path, content_bytes: bytes):
        """Verify content bytes against the loaded lock entry."""

    @abstractmethod
    def scan_and_lock(self) -> PromptLock:
        """Scan tracked prompt files and write a deterministic lock file."""

    @abstractmethod
    def check_against_lock(self):
        """Check tracked prompt files against the loaded lock policy."""
