# core/video_source_screen.py - Скриншот экрана (оригинальный)
import cv2
from mss import mss
from core.video_source_base import VideoSourceBase
import numpy as np


class ScreenCaptureSource(VideoSourceBase):
    """Источник видео из скриншотов экрана"""
    
    def __init__(self, monitor_number=1, monitor_mode='monitor', max_fps=10):
        super().__init__(max_fps=max_fps)
        self.sct = mss()
        self.monitor_number = monitor_number
        self.monitor_mode = monitor_mode
        self._initialize()
        self.start_capture()
    
    def _initialize(self):
        """Инициализация захвата экрана"""
        if self.monitor_mode == 'primary':
            self.monitor = self.sct.monitors[0]
        elif self.monitor_mode == 'all':
            monitors = self.sct.monitors[1:]
            self.monitor = monitors[0] if monitors else self.sct.monitors[1]
        else:
            self.monitor = self.sct.monitors[self.monitor_number]
        
        self.width = self.monitor['width']
        self.height = self.monitor['height']
        
        print(f"✓ Захват экрана инициализирован (макс. FPS: {self.max_fps})")
        print(f"  Монитор: {self.monitor_mode if self.monitor_mode != 'monitor' else f'№{self.monitor_number}'}")
        print(f"  Размер: {self.width}x{self.height}")
    
    def _capture_impl(self):
        """Реализация захвата скриншота"""
        img = self.sct.grab(self.monitor)
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)
        return frame
    
    def release(self):
        """Освобождение ресурсов"""
        super().release()
        self.sct = None
        print("✓ Захват экрана остановлен")