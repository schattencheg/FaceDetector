# core/video_source_webcam.py - Веб-камера
import cv2
from core.video_source_base import VideoSourceBase


class WebcamSource(VideoSourceBase):
    """Источник видео с веб-камеры"""
    
    def __init__(self, camera_id=0, width=640, height=480):
        super().__init__()
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.cap = None
        self._initialize()
    
    def _initialize(self):
        """Инициализация веб-камеры"""
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            raise RuntimeError(f"Не удалось открыть веб-камеру {self.camera_id}")
        
        # Устанавливаем разрешение
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        # Получаем реальное FPS
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps <= 0:
            self.fps = 30
        
        print(f"✓ Веб-камера {self.camera_id} инициализирована ({self.width}x{self.height}, {self.fps:.1f} FPS)")
    
    def capture(self):
        """Захват кадра с веб-камеры"""
        if self.is_paused and self.last_frame is not None:
            return self.last_frame.copy()
        
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Не удалось захватить кадр с веб-камеры")
        
        self.last_frame = frame.copy()
        return frame
    
    def release(self):
        """Освобождение веб-камеры"""
        if self.cap:
            self.cap.release()
            print("✓ Веб-камера освобождена")
    
    def set_resolution(self, width, height):
        """Изменение разрешения"""
        self.width = width
        self.height = height
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
