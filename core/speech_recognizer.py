import speech_recognition as sr
import threading
import time
from queue import Queue

class SpeechRecognizer:
    """Класс для распознавания речи с ограниченным набором фраз"""
    
    # Ограниченный набор фраз для распознавания
    PHRASES = {
        # Команды управления
        'режим обучения': 'toggle_learning',
        'включи обучение': 'toggle_learning',
        'выключи обучение': 'toggle_learning',
        'обучение': 'toggle_learning',
        
        'сохранить': 'screenshot',
        'скриншот': 'screenshot',
        'сфоткай': 'screenshot',
        
        'перезагрузить': 'reload',
        'обнови': 'reload',
        
        'выход': 'exit',
        'закрой': 'exit',
        'стоп': 'exit',
        'пошли за пивом': 'exit',
        
        # Добавление лиц
        'добавить': 'add_face',
        'запомни': 'add_face',
        'это': 'add_face',
        
        # Информационные
        'информация': 'info',
        'статус': 'info',
        'сколько лиц': 'face_count'
    }
    
    # Голосовые команды на английском
    ENGLISH_PHRASES = {
        'learning mode': 'toggle_learning',
        'learn': 'toggle_learning',
        'screenshot': 'screenshot',
        'save': 'screenshot',
        'reload': 'reload',
        'refresh': 'reload',
        'exit': 'exit',
        'quit': 'exit',
        'stop': 'exit',
        'add face': 'add_face',
        'remember': 'add_face'
    }
    
    def __init__(self, language='ru-RU'):
        self.recognizer = sr.Recognizer()
        self.language = language
        self.is_listening = False
        self.command_queue = Queue()
        self.thread = None
        
        # Настройка распознавателя
        self.recognizer.energy_threshold = 300  # Порог чувствительности
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8  # Пауза между словами
        
        # Объединяем фразы
        self.all_phrases = {**self.PHRASES, **self.ENGLISH_PHRASES}
    
    def start(self):
        """Запуск распознавания в отдельном потоке"""
        if not self.is_listening:
            self.is_listening = True
            self.thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.thread.start()
            print(f"✓ Распознавание речи запущено (язык: {self.language})")
            print("  Доступные команды:")
            for phrase in list(self.PHRASES.keys())[:5]:
                print(f"    - {phrase}")
    
    def _listen_loop(self):
        """Основной цикл прослушивания"""
        with sr.Microphone() as source:
            # Адаптируемся к окружающему шуму
            print("  Калибровка микрофона...")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("  Готов к распознаванию команд!")
            
            while self.is_listening:
                try:
                    # Слушаем речь
                    print("  Слушаю...", end='\r')
                    audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=2)
                    
                    # Распознаем
                    try:
                        text = self.recognizer.recognize_google(audio, language=self.language)
                        text_lower = text.lower()
                        print(f"\n  Распознано: '{text_lower}'")
                        
                        # Ищем команду
                        command = self._match_command(text_lower)
                        if command:
                            self.command_queue.put(command)
                            print(f"  ✓ Команда: {command}")
                        
                    except sr.UnknownValueError:
                        pass  # Не удалось распознать
                    except sr.RequestError as e:
                        print(f"  Ошибка сервиса распознавания: {e}")
                        
                except sr.WaitTimeoutError:
                    pass  # Таймаут ожидания речи
                except Exception as e:
                    print(f"  Ошибка: {e}")
                
                time.sleep(0.1)
    
    def _match_command(self, text):
        """Сопоставление текста с командами"""
        # Точное совпадение
        if text in self.all_phrases:
            return self.all_phrases[text]
        
        # Частичное совпадение
        for phrase, command in self.all_phrases.items():
            if phrase in text or text in phrase:
                return command
        
        # Проверка на имена для добавления
        if text.startswith('это ') or text.startswith('имя '):
            name = text.split(' ', 1)[1]
            if name:
                return f'add_named_face:{name}'
        
        return None
    
    def get_command(self, block=False, timeout=None):
        """Получение команды из очереди"""
        try:
            return self.command_queue.get(block=block, timeout=timeout)
        except:
            return None
    
    def stop(self):
        """Остановка распознавания"""
        self.is_listening = False
        if self.thread:
            self.thread.join(timeout=2)
        print("✓ Распознавание речи остановлено")