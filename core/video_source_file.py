# core/video_source_file.py - Видеофайл
import cv2
from core.video_source_base import VideoSourceBase


class VideoFileSource(VideoSourceBase):
    """Источник видео из файла"""
    
    def __init__(self, file_path, loop=False):
        super().__init__()
        self.file_path = file_path
        self.loop = loop
        self.cap = None
        self._initialize()
    
    def _initialize(self):
        """Инициализация видеофайла"""
        self.cap = cv2.VideoCapture(self.file_path)
        if not self.cap.isOpened():
            raise RuntimeError(f"Не удалось открыть видеофайл: {self.file_path}")
        
        # Получаем информацию о видео
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / self.fps if self.fps > 0 else 0
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"✓ Видеофайл загружен: {self.file_path}")
        print(f"  Размер: {self.width}x{self.height}, FPS: {self.fps:.1f}")
        print(f"  Кадров: {self.total_frames}, Длительность: {self.duration:.1f} сек")
    
    def capture(self):
        """Захват кадра из видеофайла"""
        if self.is_paused and self.last_frame is not None:
            return self.last_frame.copy()
        
        ret, frame = self.cap.read()
        
        if not ret:
            if self.loop:
                # Перематываем в начало
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if not ret:
                    raise RuntimeError("Не удалось перемотать видео")
            else:
                raise StopIteration("Видео закончилось")
        
        self.last_frame = frame.copy()
        return frame
    
    def release(self):
        """Освобождение видеофайла"""
        if self.cap:
            self.cap.release()
            print("✓ Видеофайл освобожден")
    
    def get_current_position(self):
        """Получение текущей позиции в секундах"""
        if self.cap:
            current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            return current_frame / self.fps if self.fps > 0 else 0
        return 0
    
    def seek(self, seconds):
        """Перемотка на указанную секунду"""
        if self.cap and seconds >= 0:
            frame_number = int(seconds * self.fps)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
