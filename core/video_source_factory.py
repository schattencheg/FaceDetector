# core/video_source_factory.py - Фабрика для создания источников
from core.video_source_file import VideoFileSource
from core.video_source_image import StaticImageSource
from core.video_source_screen import ScreenCaptureSource
from core.video_source_webcam import WebcamSource


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

