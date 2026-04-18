from __future__ import annotations

import os
import shutil
from pathlib import Path


class JavaFinder:
    @staticmethod
    def find(configured_path: str = "", base_dir: Path | None = None) -> str:
        configured = JavaFinder.resolve(configured_path)
        if configured:
            return configured

        managed = JavaFinder.find_managed(base_dir)
        if managed:
            return managed

        java_home = os.getenv("JAVA_HOME")
        if java_home:
            candidate = JavaFinder.resolve(Path(java_home) / "bin" / "javaw.exe")
            if candidate:
                return candidate
            candidate = JavaFinder.resolve(Path(java_home) / "bin" / "java.exe")
            if candidate:
                return candidate

        from_path = shutil.which("javaw") or shutil.which("java")
        return JavaFinder.resolve(from_path)

    @staticmethod
    def resolve(java_path: str | Path | None) -> str:
        if not java_path:
            return ""

        path = Path(java_path)
        if not path.exists():
            return ""

        if path.is_dir():
            for name in ("javaw.exe", "java.exe", "javaw", "java"):
                candidate = path / "bin" / name
                if candidate.exists():
                    return str(candidate.resolve())
            return ""

        lower_name = path.name.lower()
        if lower_name in {"java", "java.exe"}:
            javaw_path = path.with_name("javaw.exe")
            if javaw_path.exists():
                return str(javaw_path.resolve())

        return str(path.resolve())

    @staticmethod
    def find_managed(base_dir: Path | None) -> str:
        if base_dir is None:
            return ""

        runtime_root = Path(base_dir) / "runtime"
        return JavaFinder.find_in_directory(runtime_root)

    @staticmethod
    def find_in_directory(root_dir: Path | None) -> str:
        if root_dir is None:
            return ""

        runtime_root = Path(root_dir)
        if not runtime_root.exists():
            return ""

        candidates: list[Path] = []
        for pattern in (
            "bin/javaw.exe",
            "bin/java.exe",
            "*/bin/javaw.exe",
            "*/bin/java.exe",
            "*/*/bin/javaw.exe",
            "*/*/bin/java.exe",
        ):
            candidates.extend(runtime_root.glob(pattern))

        for candidate in sorted(candidates, reverse=True):
            resolved = JavaFinder.resolve(candidate)
            if resolved:
                return resolved
        return ""
