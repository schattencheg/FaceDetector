import numpy as np
import face_recognition
import cv2
import threading


class FaceRecognizer:
    """Класс для распознавания лиц (свой-чужой)"""
    
    def __init__(self, face_storage):
        self.face_storage = face_storage
        self.is_learning_mode = False
        self.is_busy = False
        self.learning_mode_lock = threading.Lock()
    
    def detect_and_recognize(self, frame):
        """Одновременное обнаружение и распознавание лиц
        
        Returns:
            tuple: (face_locations, recognized_names)
            face_locations: список кортежей (top, right, bottom, left)
            recognized_names: список имен для каждого лица
        """
        if self.is_busy:
            return [], []
        
        # Конвертируем в RGB (face_recognition требует RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Находим все лица на кадре
        try:
            # Используем HOG для скорости (можно заменить на 'cnn' для точности)
            face_locations = face_recognition.face_locations(rgb_frame, model='hog')
        except Exception as e:
            print(f"Ошибка детекции лиц: {e}")
            return [], []
        
        # Получаем энкодинги (векторные представления) лиц
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        # Распознаем каждое лицо
        recognized_names = []
        for face_encoding in face_encodings:
            name = self._match_face(face_encoding)
            recognized_names.append(name)
        
        return face_locations, recognized_names
    
    def _match_face(self, face_encoding):
        """Сопоставление лица с базой данных
        
        Args:
            face_encoding: векторное представление лица
            
        Returns:
            str: имя человека или "Чужой"
        """
        # Если база пуста, все лица чужие
        if not self.face_storage.known_encodings:
            return "Чужой"
        
        # Сравниваем с известными лицами
        matches = face_recognition.compare_faces(
            self.face_storage.known_encodings, 
            face_encoding, 
            tolerance=0.6
        )
        
        if True in matches:
            first_match_index = matches.index(True)
            return self.face_storage.known_names[first_match_index]
        
        return "Чужой"
    
    def set_learning_mode(self, enabled):
        """Включение/выключение режима обучения
        
        Args:
            enabled: True - включить, False - выключить
            
        Returns:
            bool: новое состояние режима обучения
        """
        with self.learning_mode_lock:
            self.is_learning_mode = enabled
            print(f"[FaceRecognizer] Режим обучения = {self.is_learning_mode}")
            return self.is_learning_mode
    
    def is_learning(self):
        """Проверка режима обучения
        
        Returns:
            bool: True если режим обучения включен
        """
        with self.learning_mode_lock:
            return self.is_learning_mode
    
    def add_new_face(self, face_image, name):
        """Добавление нового лица в базу
        
        Args:
            face_image: изображение лица (numpy array)
            name: имя человека
            
        Returns:
            str: уникальное имя сохраненного лица
        """
        self.is_busy = True
        try:
            unique_name = self.face_storage.get_unique_name(name)
            self.face_storage.save_face(face_image, unique_name)
            print(f"[FaceRecognizer] Добавлено лицо: {unique_name}")
            return unique_name
        except Exception as e:
            print(f"[FaceRecognizer] Ошибка добавления лица: {e}")
            return None
        finally:
            self.is_busy = False
    
    def get_learning_status(self):
        """Получить статус режима обучения с информацией
        
        Returns:
            dict: статус режима обучения
        """
        with self.learning_mode_lock:
            return {
                'enabled': self.is_learning_mode,
                'busy': self.is_busy,
                'known_faces_count': len(self.face_storage.known_names)
            }
    
    def is_busy_status(self):
        """Проверка, занят ли распознаватель
        
        Returns:
            bool: True если идет добавление лица
        """
        return self.is_busy