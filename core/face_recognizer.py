import face_recognition
import cv2

class FaceRecognizer:
    """Класс для распознавания лиц (свой-чужой)"""
    
    def __init__(self, face_storage):
        self.face_storage = face_storage
        self.is_learning_mode = False
        self.is_busy = False
    
    def recognize(self, frame, faces):
        """Распознавание всех лиц на кадре"""
        if self.is_busy or not faces.any():
            return []
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        recognized_names = []
        for face_encoding in face_encodings:
            name = self._match_face(face_encoding)
            recognized_names.append(name)
        
        return recognized_names
    
    def _match_face(self, face_encoding):
        """Сопоставление лица с базой"""
        if not self.face_storage.known_encodings:
            return "Чужой"
        
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
        """Включение/выключение режима обучения"""
        self.is_learning_mode = enabled
        return self.is_learning_mode
    
    def add_new_face(self, face_image, name):
        """Добавление нового лица в базу"""
        self.is_busy = True
        try:
            unique_name = self.face_storage.get_unique_name(name)
            self.face_storage.save_face(face_image, unique_name)
            return unique_name
        finally:
            self.is_busy = False