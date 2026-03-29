# Raramba Launcher

Лаунчер Minecraft (PySide6) под одну сборку `1.12.2`.

## Локальный запуск
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## Сборка portable .exe
Самый быстрый способ:
```powershell
.\build_portable.ps1
```

После сборки:
- `dist\RarambaLauncher\RarambaLauncher.exe`
- настройки portable лежат рядом с exe: `dist\RarambaLauncher\data\config.json`
- фон подхватывается из `dist\RarambaLauncher\assets\background.png`

## Структура
- `main.py` - точка входа
- `launcher/app.py` - инициализация приложения
- `launcher/core/*` - бизнес-логика
- `launcher/ui/main_window.py` - интерфейс
- `build_portable.ps1` - сборка portable-версии
