# Bookworm 🐛 — Audiobook Reader

Локална web услуга за четене на книги (PDF/EPUB) с Piper TTS.
Хостната на Raspberry Pi, достъпна от всяко устройство в мрежата.

## Изисквания

- Piper вече инсталиран в `~/piper/piper`
- Piper voice модел в `~/piper-voices/` (например `no_NO-talesyntese-medium.onnx`)
- Python 3.11+

## Инсталация

```bash
# 1. Клонирай / копирай проекта
mkdir -p ~/Projects/bookworm
cp -r /path/to/bookworm/* ~/Projects/bookworm/
cd ~/Projects/bookworm

# 2. Виртуална среда
python3 -m venv venv
source venv/bin/activate

# 3. Зависимости
pip install -r requirements.txt

# 4. Тест стартиране
uvicorn main:app --host 0.0.0.0 --port 8001

# Отвори http://<PI_IP>:8001
```

## Systemd service (автоматичен старт)

```bash
sudo cp bookworm.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable bookworm
sudo systemctl start bookworm

# Проверка
sudo systemctl status bookworm
sudo journalctl -u bookworm -f
```

## Структура

```
bookworm/
├── main.py                  # FastAPI app
├── requirements.txt
├── bookworm.service          # systemd
├── app/
│   ├── db.py                # SQLite модели
│   ├── parser.py            # PDF/EPUB парсър
│   ├── routers/
│   │   ├── library.py       # Качване, библиотека
│   │   ├── reader.py        # Четец, прогрес
│   │   └── tts.py           # Piper TTS endpoint
│   └── templates/
│       ├── library.html     # Библиотека
│       └── reader.html      # Четец
└── data/
    ├── bookworm.db          # SQLite база
    ├── books/               # Качени книги
    └── tts_cache/           # Кеш на генерирано аудио
```

## Настройки на Piper TTS

По подразбиране се ползва първият намерен `.onnx` модел в `~/piper-voices/`.
Скоростта се управлява от слайдера в интерфейса (0.5× до 2.0×).

## Клавишни комбинации (в четеца)

| Клавиш | Действие |
|--------|----------|
| Space | Пауза / Продължи |
| → | Следващ параграф |
| ← | Предишен параграф |

## Порт

По подразбиране: **8001** (norsk-drill е на 8000)
