# core/video_source_base.py - Базовый класс
from abc import ABC, abstractmethod
import cv2
import time
import threading
from queue import Queue

class VideoSourceBase(ABC):
    """Абстрактный базовый класс для всех источников видео"""
    
    def __init__(self, max_fps=15):
        self.last_frame = None
        self.is_paused = False
        self.max_fps = max_fps  # Максимальное количество кадров в секунду
        self.frame_interval = 1.0 / max_fps if max_fps > 0 else 0
        self.last_frame_time = 0
        self.frame_queue = Queue(maxsize=2)  # Ограниченная очередь для кадров
        self.is_running = False
        self.capture_thread = None
        
    @abstractmethod
    def _capture_impl(self):
        """Реальная реализация захвата кадра (должна быть реализована в наследниках)"""
        pass
    
    def start_capture(self):
        """Запуск потока захвата видео"""
        if not self.is_running:
            self.is_running = True
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            print(f"✓ Поток захвата запущен (макс. FPS: {self.max_fps})")
    
    def _capture_loop(self):
        """Цикл захвата кадров в отдельном потоке"""
        while self.is_running:
            if not self.is_paused:
                current_time = time.time()
                
                # Ограничение FPS
                if current_time - self.last_frame_time >= self.frame_interval:
                    try:
                        frame = self._capture_impl()
                        if frame is not None:
                            # Очищаем очередь если переполнена
                            if self.frame_queue.full():
                                try:
                                    self.frame_queue.get_nowait()
                                except:
                                    pass
                            self.frame_queue.put(frame)
                            self.last_frame = frame
                            self.last_frame_time = current_time
                    except Exception as e:
                        print(f"Ошибка захвата кадра: {e}")
            
            time.sleep(0.001)  # Небольшая задержка для снижения нагрузки
    
    def capture(self):
        """Получение последнего кадра из очереди (неблокирующий)"""
        try:
            if self.is_paused and self.last_frame is not None:
                return self.last_frame.copy()
            
            # Берем кадр из очереди без блокировки
            frame = self.frame_queue.get_nowait()
            return frame
        except:
            # Если очередь пуста, возвращаем последний кадр
            return self.last_frame.copy() if self.last_frame is not None else None
    
    def pause(self):
        """Пауза захвата"""
        self.is_paused = True
    
    def resume(self):
        """Возобновление захвата"""
        self.is_paused = False
    
    def get_last_frame(self):
        """Получение последнего кадра"""
        return self.last_frame.copy() if self.last_frame is not None else None
    
    def stop_capture(self):
        """Остановка потока захвата"""
        self.is_running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
    
    @abstractmethod
    def release(self):
        """Освобождение ресурсов"""
        self.stop_capture()
    
    def get_info(self):
        """Получение информации об источнике"""
        return {
            'type': self.__class__.__name__,
            'max_fps': self.max_fps,
            'is_paused': self.is_paused,
            'is_running': self.is_running
        }