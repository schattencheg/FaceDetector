# core/video_source_base.py - Базовый класс
from abc import ABC, abstractmethod
import cv2
import numpy as np

class VideoSourceBase(ABC):
    """Абстрактный базовый класс для всех источников видео"""
    
    def __init__(self):
        self.last_frame = None
        self.is_paused = False
        self.fps = 30
    
    @abstractmethod
    def capture(self):
        """Захват кадра (должен быть реализован в наследниках)"""
        pass
    
    def pause(self):
        """Пауза захвата"""
        self.is_paused = True
    
    def resume(self):
        """Возобновление захвата"""
        self.is_paused = False
    
    def get_last_frame(self):
        """Получение последнего кадра"""
        return self.last_frame.copy() if self.last_frame is not None else None
    
    @abstractmethod
    def release(self):
        """Освобождение ресурсов"""
        pass
    
    def get_info(self):
        """Получение информации об источнике"""
        return {
            'type': self.__class__.__name__,
            'fps': self.fps,
            'is_paused': self.is_paused
        }
