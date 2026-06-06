emotion_recognition/
├── main.py                 # Главный файл
├── config.json            # Сохраняемая конфигурация (создается автоматически)
├── test_image.jpg         # Тестовое изображение (создается автоматически)
├── gui/
│   └── config_window.py   # Окно конфигурации
├── core/
│   ├── video_source_base.py
│   ├── video_source_webcam.py
│   ├── video_source_file.py
│   ├── video_source_image.py
│   ├── video_source_screen.py
│   ├── video_source_factory.py
│   ├── face_detector.py
│   ├── face_recognizer.py
│   ├── emotion_analyzer.py
│   ├── dialog_manager.py
│   ├── drawer.py
│   ├── audio_source.py
│   ├── speech_recognizer.py
│   └── audio_commands.py
├── input/
│   └── key_handler.py
├── storage/
│   └── face_storage.py
├── utils/
│   └── text_renderer.py
├── known_faces/           # Папка с известными лицами
└── screenshots/           # Папка со скриншотами