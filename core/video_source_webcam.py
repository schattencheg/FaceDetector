# core/video_source_webcam.py - Веб-камера
import cv2
from core.video_source_base import VideoSourceBase


class WebcamSource(VideoSourceBase):
    """Источник видео с веб-камеры"""
    
    def __init__(self, camera_id=0, width=640, height=480, max_fps=15):
        super().__init__(max_fps=max_fps)
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.cap = None
        self._initialize()
        self.start_capture()
    
    def _initialize(self):
        """Инициализация веб-камеры"""
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            raise RuntimeError(f"Не удалось открыть веб-камеру {self.camera_id}")
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        if actual_fps > 0:
            print(f"✓ Веб-камера {self.camera_id} инициализирована ({self.width}x{self.height}, {actual_fps:.1f} FPS)")
    
    def _capture_impl(self):
        """Реализация захвата кадра"""
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Не удалось захватить кадр с веб-камеры")
        return frame
    
    def release(self):
        """Освобождение веб-камеры"""
        super().release()
        if self.cap:
            self.cap.release()
            print("✓ Веб-камера освобождена")