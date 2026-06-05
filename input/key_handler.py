import threading
import time
import keyboard

class KeyHandler:
    """Класс для обработки клавиш в отдельном потоке"""
    
    def __init__(self):
        self.running = True
        self.keys = {
            'q': False,
            'l': False,
            's': False,
            'r': False,
            'enter': False
        }
        self.thread = None
    
    def start(self):
        """Запуск обработки клавиш"""
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()
    
    def _listen(self):
        """Прослушивание клавиш"""
        while self.running:
            try:
                for key in self.keys:
                    if keyboard.is_pressed(key):
                        if not self.keys[key]:
                            self.keys[key] = True
                        time.sleep(0.15)  # Защита от дребезга
                        break
                    else:
                        self.keys[key] = False
                
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
            return True
        return False
    
    def stop(self):
        """Остановка обработчика"""
        self.running = False