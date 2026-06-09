# core/video_source_file.py - Видеофайл
import cv2
from core.video_source_base import VideoSourceBase


class VideoFileSource(VideoSourceBase):
    """Источник видео из файла"""
    
    def __init__(self, file_path, loop=False, max_fps=15):
        super().__init__(max_fps=max_fps)
        self.file_path = file_path
        self.loop = loop
        self.cap = None
        self._initialize()
        self.start_capture()
    
    def _initialize(self):
        """Инициализация видеофайла"""
        self.cap = cv2.VideoCapture(self.file_path)
        if not self.cap.isOpened():
            raise RuntimeError(f"Не удалось открыть видеофайл: {self.file_path}")
        
        self.original_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / self.original_fps if self.original_fps > 0 else 0
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"✓ Видеофайл загружен: {self.file_path}")
        print(f"  Размер: {self.width}x{self.height}, FPS: {self.original_fps:.1f}")
        print(f"  Кадров: {self.total_frames}, Длительность: {self.duration:.1f} сек")
        print(f"  Обработка с ограничением: {self.max_fps} FPS")
    
    def _capture_impl(self):
        """Реализация захвата кадра из видеофайла"""
        ret, frame = self.cap.read()
        
        if not ret:
            if self.loop:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if not ret:
                    raise RuntimeError("Не удалось перемотать видео")
            else:
                raise StopIteration("Видео закончилось")
        
        return frame
    
    def release(self):
        """Освобождение видеофайла"""
        super().release()
        if self.cap:
            self.cap.release()
            print("✓ Видеофайл освобожден")