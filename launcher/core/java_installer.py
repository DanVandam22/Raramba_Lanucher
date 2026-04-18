from __future__ import annotations

from dataclasses import dataclass
import platform
from pathlib import Path
import shutil
import tempfile
from typing import Callable
import zipfile

import requests

from launcher.core.config_manager import ConfigManager
from launcher.core.java_finder import JavaFinder


@dataclass(slots=True)
class JavaInstallResult:
    ok: bool
    message: str
    details: str = ""
    java_path: str = ""


class JavaInstaller:
    FEATURE_RELEASE = 17

    def __init__(self, config_manager: ConfigManager) -> None:
        self._config_manager = config_manager

    def install(
        self,
        progress_callback: Callable[[int], None] | None = None,
        max_callback: Callable[[int], None] | None = None,
        status_callback: Callable[[str], None] | None = None,
    ) -> JavaInstallResult:
        runtime_root = self._config_manager.base_dir / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)

        managed_java = JavaFinder.find_managed(self._config_manager.base_dir)
        if managed_java:
            self._config_manager.update(java_path=managed_java)
            return JavaInstallResult(
                ok=True,
                message="Java уже подготовлена.",
                java_path=managed_java,
            )

        try:
            metadata = self._fetch_release_metadata()
            binary = self._extract_package_info(metadata)
            version_name = str(metadata["version_data"]["openjdk_version"])
            package_name = str(binary["name"])
            package_url = str(binary["link"])

            install_dir = runtime_root / f"temurin-jre-{version_name.replace('+', '_')}"
            java_path = JavaFinder.find_managed(install_dir.parent)
            if java_path:
                self._config_manager.update(java_path=java_path)
                return JavaInstallResult(
                    ok=True,
                    message="Java уже установлена.",
                    java_path=java_path,
                )

            with tempfile.TemporaryDirectory(prefix="raramba-java-") as temp_dir_raw:
                temp_dir = Path(temp_dir_raw)
                archive_path = temp_dir / package_name

                self._set_status(status_callback, "Скачиваем Java 17...")
                self._download_archive(
                    package_url,
                    archive_path,
                    progress_callback=progress_callback,
                    max_callback=max_callback,
                )

                extract_dir = temp_dir / "extracted"
                extract_dir.mkdir(parents=True, exist_ok=True)
                self._set_status(status_callback, "Распаковываем Java...")
                self._extract_archive(
                    archive_path,
                    extract_dir,
                    progress_callback=progress_callback,
                    max_callback=max_callback,
                )

                extracted_java = JavaFinder.find_in_directory(extract_dir)
                if not extracted_java:
                    return JavaInstallResult(
                        ok=False,
                        message="Не удалось найти java.exe после распаковки Java.",
                        details=f"Архив: {package_name}",
                    )

                if install_dir.exists():
                    shutil.rmtree(install_dir)
                source_root = Path(extracted_java).resolve().parents[1]
                shutil.move(str(source_root), str(install_dir))

            final_java_path = JavaFinder.find_managed(runtime_root.parent)
            if not final_java_path:
                return JavaInstallResult(
                    ok=False,
                    message="Java скачана, но путь к javaw.exe не найден.",
                    details=f"Папка установки: {install_dir}",
                )

            self._config_manager.update(java_path=final_java_path)
            self._set_status(status_callback, "Java готова к запуску.")
            return JavaInstallResult(
                ok=True,
                message="Java 17 успешно установлена.",
                java_path=final_java_path,
            )
        except requests.RequestException as exc:
            return JavaInstallResult(
                ok=False,
                message="Не удалось скачать Java 17.",
                details=str(exc),
            )
        except zipfile.BadZipFile as exc:
            return JavaInstallResult(
                ok=False,
                message="Архив Java повреждён или имеет неверный формат.",
                details=str(exc),
            )
        except Exception as exc:
            return JavaInstallResult(
                ok=False,
                message="Не удалось установить Java 17.",
                details=f"{type(exc).__name__}: {exc}",
            )

    def _fetch_release_metadata(self) -> dict:
        arch = self._get_architecture()
        url = (
            f"https://api.adoptium.net/v3/assets/feature_releases/{self.FEATURE_RELEASE}/ga"
            f"?architecture={arch}&heap_size=normal&image_type=jre&jvm_impl=hotspot"
            f"&os=windows&page=0&page_size=1&project=jdk&sort_method=DEFAULT"
            f"&sort_order=DESC&vendor=eclipse"
        )
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        assets = response.json()
        if not isinstance(assets, list) or not assets:
            raise RuntimeError("Adoptium API не вернуло доступных сборок Java 17.")
        metadata = assets[0]
        if not isinstance(metadata, dict):
            raise RuntimeError("Adoptium API вернуло неожиданный ответ.")
        return metadata

    @staticmethod
    def _extract_package_info(metadata: dict) -> dict:
        binaries = metadata.get("binaries")
        if not isinstance(binaries, list) or not binaries:
            raise RuntimeError("В ответе Adoptium нет бинарных файлов для загрузки.")
        first = binaries[0]
        if not isinstance(first, dict):
            raise RuntimeError("Некорректное описание бинарного файла Java.")
        package = first.get("package")
        if not isinstance(package, dict):
            raise RuntimeError("В ответе Adoptium нет zip-пакета Java.")
        if "link" not in package or "name" not in package:
            raise RuntimeError("Недостаточно данных для загрузки Java.")
        return package

    @staticmethod
    def _download_archive(
        url: str,
        archive_path: Path,
        progress_callback: Callable[[int], None] | None,
        max_callback: Callable[[int], None] | None,
    ) -> None:
        with requests.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()
            total_bytes = int(response.headers.get("Content-Length", "0") or "0")
            if max_callback is not None:
                max_callback(max(total_bytes, 1))
            downloaded = 0
            with archive_path.open("wb") as file_obj:
                for chunk in response.iter_content(chunk_size=1024 * 256):
                    if not chunk:
                        continue
                    file_obj.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback is not None:
                        progress_callback(downloaded)

    @staticmethod
    def _extract_archive(
        archive_path: Path,
        extract_dir: Path,
        progress_callback: Callable[[int], None] | None,
        max_callback: Callable[[int], None] | None,
    ) -> None:
        with zipfile.ZipFile(archive_path) as archive:
            members = archive.infolist()
            if max_callback is not None:
                max_callback(max(len(members), 1))
            for index, member in enumerate(members, start=1):
                archive.extract(member, extract_dir)
                if progress_callback is not None:
                    progress_callback(index)

    @staticmethod
    def _set_status(status_callback: Callable[[str], None] | None, text: str) -> None:
        if status_callback is not None:
            status_callback(text)

    @staticmethod
    def _get_architecture() -> str:
        machine = platform.machine().lower()
        if machine in {"amd64", "x86_64", "x64"}:
            return "x64"
        if machine in {"arm64", "aarch64"}:
            return "aarch64"
        return "x64"
