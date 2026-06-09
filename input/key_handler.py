import threading
import time
import keyboard

class KeyHandler:
    def __init__(self):
        self.running = True
        self.keys = {
            'q': False,
            'l': False,
            's': False,
            'r': False,
            'enter': False
        }
        self.last_processed = {}  # Для отслеживания обработанных нажатий
        self.thread = None
    
    def start(self):
        """Запуск обработки клавиш"""
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()
    
    def _listen(self):
        """Прослушивание клавиш"""
        last_key_state = {}
        
        while self.running:
            try:
                for key in self.keys:
                    is_pressed = keyboard.is_pressed(key)
                    last_state = last_key_state.get(key, False)
                    
                    # Срабатываем ТОЛЬКО при смене состояния с False на True
                    if is_pressed and not last_state:
                        if not self.keys[key]:  # Если еще не обработано
                            self.keys[key] = True
                            print(f"🔑 Клавиша {key} нажата")  # Отладка
                    # Сбрасываем флаг когда клавиша отпущена
                    elif not is_pressed and last_state:
                        self.keys[key] = False
                    
                    last_key_state[key] = is_pressed
                
                time.sleep(0.02)
            except:
                pass

    def is_pressed(self, key):
        """Проверка нажатия клавиши"""
        return self.keys.get(key, False)
    
    def consume(self, key):
        """Потребление нажатия клавиши (сброс флага)"""
        if self.keys.get(key, False):
            self.keys[key] = False
            print(f"✅ Клавиша {key} обработана и сброшена")  # Отладка
            return True
        return False
    
    def stop(self):
        """Остановка обработчика"""
        self.running = False