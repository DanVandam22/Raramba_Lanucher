from __future__ import annotations

import os
import shutil
from pathlib import Path


class JavaFinder:
    @staticmethod
    def find() -> str:
        java_home = os.getenv("JAVA_HOME")
        if java_home:
            candidate = Path(java_home) / "bin" / "javaw.exe"
            if candidate.exists():
                return str(candidate)
            candidate = Path(java_home) / "bin" / "java.exe"
            if candidate.exists():
                return str(candidate)

        from_path = shutil.which("javaw") or shutil.which("java")
        return from_path or ""
