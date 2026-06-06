# core/video_source_screen.py - Скриншот экрана (оригинальный)
import cv2
from mss import mss
from core.video_source_base import VideoSourceBase


class ScreenCaptureSource(VideoSourceBase):
    """Источник видео из скриншотов экрана"""
    
    def __init__(self, monitor_number=1, monitor_mode='monitor'):
        """
        monitor_mode: 'monitor' - конкретный монитор, 'all' - все мониторы, 'primary' - главный
        """
        super().__init__()
        self.sct = mss()
        self.monitor_number = monitor_number
        self.monitor_mode = monitor_mode
        self._initialize()
    
    def _initialize(self):
        """Инициализация захвата экрана"""
        if self.monitor_mode == 'primary':
            self.monitor = self.sct.monitors[0]  # Главный монитор
        elif self.monitor_mode == 'all':
            # Объединяем все мониторы
            monitors = self.sct.monitors[1:]  # Пропускаем первый (виртуальный)
            if monitors:
                self.monitor = monitors[0]
            else:
                self.monitor = self.sct.monitors[1]
        else:
            self.monitor = self.sct.monitors[self.monitor_number]
        
        self.width = self.monitor['width']
        self.height = self.monitor['height']
        self.fps = 30  # Ограничиваем для снижения нагрузки
        
        print(f"✓ Захват экрана инициализирован")
        print(f"  Монитор: {self.monitor_mode if self.monitor_mode != 'monitor' else f'№{self.monitor_number}'}")
        print(f"  Размер: {self.width}x{self.height}")
    
    def capture(self):
        """Захват скриншота"""
        if self.is_paused and self.last_frame is not None:
            return self.last_frame.copy()
        
        img = self.sct.grab(self.monitor)
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)
        self.last_frame = frame.copy()
        return frame
    
    def release(self):
        """Освобождение ресурсов"""
        self.sct = None
        print("✓ Захват экрана остановлен")
    
    def change_monitor(self, monitor_number):
        """Смена монитора"""
        self.monitor_number = monitor_number
        self._initialize()

