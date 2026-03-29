# Raramba Launcher

<p align="center">
  <img src="assets/logo.png" alt="Raramba Launcher" width="220">
</p>

<p align="center">
  Лаунчер Minecraft для сборки <code>1.12.2</code> с авторизацией через <code>Ely.by</code>,
  аккуратным desktop-интерфейсом на <code>PySide6</code> и релизной сборкой в один <code>.exe</code>.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.14-6b4baa?style=flat-square" alt="Python 3.14">
  <img src="https://img.shields.io/badge/PySide6-Desktop_UI-8c6cff?style=flat-square" alt="PySide6">
  <img src="https://img.shields.io/badge/Minecraft-1.12.2-4aa96c?style=flat-square" alt="Minecraft 1.12.2">
  <img src="https://img.shields.io/badge/Auth-Ely.by-b784ff?style=flat-square" alt="Ely.by">
</p>

## About

Raramba Launcher сделан как атмосферный и цельный лаунчер под конкретную сборку Minecraft.
Проект сочетает в себе desktop UX, авторизацию Ely.by, настраиваемый запуск клиента и
one-file релизную сборку для удобной раздачи в узком кругу пользователей.

## Features

- Авторизация через `Ely.by`
- Запуск `Minecraft 1.12.2`
- Сборка в один `.exe`
- Выбор директории игры
- Настройка выделения ОЗУ
- Показ логов запуска и открытие папки логов
- Компактная панель настроек
- Кастомный интерфейс на `PySide6`

## Stack

- `Python`
- `PySide6`
- `minecraft-launcher-lib`
- `Ely.by OAuth`
- `PyInstaller`

## Project Structure

- [main.py](main.py) — точка входа
- [launcher/app.py](launcher/app.py) — инициализация приложения
- [launcher/core](launcher/core) — конфиг, запуск игры, Ely.by, профили
- [launcher/ui](launcher/ui) — окно, панели, контроллеры и тема
- [assets](assets) — графика, иконки, шрифты и вспомогательные файлы
- [tests](tests) — базовые unit-тесты

## Local Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## Build One-File EXE

```powershell
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name "Raramba Launcher" --icon assets/ico.ico --add-data "assets;assets" main.py
```

Готовый файл появится здесь:

- [dist/Raramba Launcher.exe](dist/Raramba%20Launcher.exe)

## Ely.by

Для запуска через Ely.by лаунчеру нужен `authlib-injector`.

Файл можно положить в папку:

- `assets/authlib-injector.jar`
- или в виде версионированного файла, например `assets/authlib-injector-1.2.7.jar`

## Release Notes

Проект ориентирован на аккуратный приватный релиз:

- portable-конфиг
- one-file сборка
- поддержка Ely.by
- мягкая обработка сетевых ошибок и повторных попыток скачивания

## License

Проект используется как частный launcher build.
