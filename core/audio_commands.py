import threading
import time

class AudioCommandHandler:
    """Обработчик голосовых команд для приложения"""
    
    def __init__(self, app):
        self.app = app
        self.audio_source = None
        self.speech_recognizer = None
        self.is_running = False
        self.thread = None
        
        # Состояние ожидания имени для добавления
        self.waiting_for_name = False
        self.pending_face = None
    
    def start(self):
        """Запуск аудио-системы"""
        try:
            from core.audio_source import AudioSource
            from core.speech_recognizer import SpeechRecognizer
            
            self.audio_source = AudioSource()
            self.speech_recognizer = SpeechRecognizer()
            
            # Запускаем в отдельных потоках
            self.audio_source.start()
            self.speech_recognizer.start()
            
            self.is_running = True
            self.thread = threading.Thread(target=self._process_commands, daemon=True)
            self.thread.start()
            
            return True
        except Exception as e:
            print(f"❌ Ошибка инициализации аудио: {e}")
            return False
    
    def _process_commands(self):
        """Обработка команд из очереди"""
        while self.is_running:
            command = self.speech_recognizer.get_command(timeout=0.5)
            
            if command:
                self._execute_command(command)
            
            # Если ждем имя для лица, проверяем аудио
            if self.waiting_for_name and self.pending_face:
                audio_chunk = self.audio_source.get_audio_chunk(duration=2)
                if audio_chunk is not None:
                    # Пытаемся распознать имя
                    name = self._recognize_name(audio_chunk)
                    if name:
                        self.app.add_new_face_direct(self.pending_face, name)
                        self.waiting_for_name = False
                        self.pending_face = None
            
            time.sleep(0.1)
    
    def _execute_command(self, command):
        """Выполнение голосовой команды"""
        if command == 'toggle_learning':
            self.app.toggle_learning_mode()
            print("🔊 Голосовая команда: переключение режима обучения")
            
        elif command == 'screenshot':
            self.app.take_screenshot()
            print("🔊 Голосовая команда: сохранение скриншота")
            
        elif command == 'reload':
            self.app.reload_faces()
            print("🔊 Голосовая команда: перезагрузка базы лиц")
            
        elif command == 'exit':
            print("🔊 Голосовая команда: выход из программы")
            self.app.quit()
            
        elif command == 'add_face':
            print("🔊 Голосовая команда: добавление лица")
            # Активируем режим ожидания имени
            self.app.activate_voice_learning()
            
        elif command == 'info':
            self.app.print_info()
            
        elif command == 'face_count':
            count = self.app.get_face_count()
            print(f"🔊 В базе {count} лиц")
            
        elif command.startswith('add_named_face:'):
            name = command.split(':', 1)[1]
            print(f"🔊 Добавление лица с именем: {name}")
            self.app.add_new_face_direct(self.pending_face, name)
            self.pending_face = None
    
    def _recognize_name(self, audio_chunk):
        """Распознавание имени из аудио"""
        # Упрощенная версия - можно использовать тот же SpeechRecognizer
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            
            # Конвертируем numpy array в аудио
            audio_data = (audio_chunk * 32767).astype(np.int16).tobytes()
            audio = sr.AudioData(audio_data, self.audio_source.sample_rate, 2)
            
            text = recognizer.recognize_google(audio, language='ru-RU')
            print(f"  Распознано имя: {text}")
            return text
        except:
            return None
    
    def set_pending_face(self, face_image):
        """Установка лица для добавления"""
        self.pending_face = face_image
        self.waiting_for_name = True
        
        # Голосовое уведомление (опционально)
        self._speak("Скажите имя для этого лица")
    
    def _speak(self, text):
        """Голосовое уведомление (опционально)"""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except:
            pass
    
    def stop(self):
        """Остановка аудио-системы"""
        self.is_running = False
        if self.audio_source:
            self.audio_source.stop()
        if self.speech_recognizer:
            self.speech_recognizer.stop()