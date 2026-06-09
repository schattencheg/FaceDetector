# core/video_source_image.py - Статичное изображение
import cv2
from core.video_source_base import VideoSourceBase


class StaticImageSource(VideoSourceBase):
    """Источник видео из статичного изображения"""
    
    def __init__(self, image_path, max_fps=5):  # Для изображения достаточно 5 FPS
        super().__init__(max_fps=max_fps)
        self.image_path = image_path
        self.image = None
        self._initialize()
        self.start_capture()
    
    def _initialize(self):
        """Загрузка изображения"""
        self.image = cv2.imread(self.image_path)
        if self.image is None:
            raise RuntimeError(f"Не удалось загрузить изображение: {self.image_path}")
        
        self.height, self.width = self.image.shape[:2]
        self.last_frame = self.image.copy()
        
        print(f"✓ Статичное изображение загружено: {self.image_path}")
        print(f"  Размер: {self.width}x{self.height}, Обработка: {self.max_fps} FPS")
    
    def _capture_impl(self):
        """Возвращает одно и то же изображение"""
        return self.image.copy()
    
    def release(self):
        """Освобождение ресурсов"""
        super().release()
        self.image = None
        print("✓ Изображение выгружено")