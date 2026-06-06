# core/video_source_image.py - Статичное изображение
import cv2
from core.video_source_base import VideoSourceBase


class StaticImageSource(VideoSourceBase):
    """Источник видео из статичного изображения"""
    
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        self.image = None
        self._initialize()
    
    def _initialize(self):
        """Загрузка изображения"""
        self.image = cv2.imread(self.image_path)
        if self.image is None:
            raise RuntimeError(f"Не удалось загрузить изображение: {self.image_path}")
        
        self.height, self.width = self.image.shape[:2]
        self.fps = 1  # Статичное изображение
        self.last_frame = self.image.copy()
        
        print(f"✓ Статичное изображение загружено: {self.image_path}")
        print(f"  Размер: {self.width}x{self.height}")
    
    def capture(self):
        """Возвращает одно и то же изображение"""
        if self.is_paused and self.last_frame is not None:
            return self.last_frame.copy()
        
        # Всегда возвращаем копию изображения
        frame = self.image.copy()
        self.last_frame = frame.copy()
        return frame
    
    def release(self):
        """Освобождение ресурсов"""
        self.image = None
        print("✓ Изображение выгружено")
    
    def change_image(self, image_path):
        """Смена изображения на лету"""
        self.image_path = image_path
        self._initialize()

