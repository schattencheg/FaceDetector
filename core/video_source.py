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


# core/video_source_webcam.py - Веб-камера
import cv2

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


# core/video_source_file.py - Видеофайл
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


# core/video_source_image.py - Статичное изображение
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


# core/video_source_screen.py - Скриншот экрана (оригинальный)
from mss import mss

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


# core/video_source_factory.py - Фабрика для создания источников
class VideoSourceFactory:
    """Фабрика для создания источников видео"""
    
    @staticmethod
    def create_webcam(camera_id=0, width=640, height=480):
        """Создание источника с веб-камеры"""
        return WebcamSource(camera_id, width, height)
    
    @staticmethod
    def create_video_file(file_path, loop=False):
        """Создание источника из видеофайла"""
        return VideoFileSource(file_path, loop)
    
    @staticmethod
    def create_image(image_path):
        """Создание источника из статичного изображения"""
        return StaticImageSource(image_path)
    
    @staticmethod
    def create_screen_capture(monitor_number=1, monitor_mode='monitor'):
        """Создание источника из скриншотов экрана"""
        return ScreenCaptureSource(monitor_number, monitor_mode)
    
    @staticmethod
    def create_from_config(config):
        """
        Создание источника на основе конфигурации
        config = {
            'type': 'webcam', 'video', 'image', 'screen'
            'params': {...}
        }
        """
        source_type = config.get('type', 'screen')
        params = config.get('params', {})
        
        if source_type == 'webcam':
            return VideoSourceFactory.create_webcam(
                camera_id=params.get('camera_id', 0),
                width=params.get('width', 640),
                height=params.get('height', 480)
            )
        elif source_type == 'video':
            return VideoSourceFactory.create_video_file(
                file_path=params.get('file_path'),
                loop=params.get('loop', False)
            )
        elif source_type == 'image':
            return VideoSourceFactory.create_image(
                image_path=params.get('image_path')
            )
        elif source_type == 'screen':
            return VideoSourceFactory.create_screen_capture(
                monitor_number=params.get('monitor_number', 1),
                monitor_mode=params.get('monitor_mode', 'monitor')
            )
        else:
            raise ValueError(f"Неизвестный тип источника: {source_type}")

