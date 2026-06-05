emotion_recognition/
├── main.py                 # Главный файл
├── core/
│   ├── __init__.py
│   ├── video_source.py    # Захват видео (скриншоты)
│   ├── face_detector.py   # Детектор лиц (Haar Cascade)
│   ├── face_recognizer.py # Распознавание лиц (свой-чужой)
│   ├── emotion_analyzer.py # Анализ эмоций
│   ├── drawer.py          # Отрисовка графики
│   └── dialog_manager.py  # Управление диалогами
├── input/
│   ├── __init__.py
│   └── key_handler.py     # Обработка клавиш
├── storage/
│   ├── __init__.py
│   └── face_storage.py    # Хранение лиц
└── utils/
    ├── __init__.py
    └── text_renderer.py   # Рендеринг текста с кириллицей