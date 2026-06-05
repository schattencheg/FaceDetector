import os
import cv2
import face_recognition

class FaceStorage:
    """Класс для хранения и загрузки известных лиц"""
    
    def __init__(self, storage_dir="known_faces"):
        self.storage_dir = storage_dir
        self.known_encodings = []
        self.known_names = []
        self._create_storage()
        self.load_faces()
    
    def _create_storage(self):
        """Создание директории для хранения"""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
            print(f"Создана директория {self.storage_dir}")
    
    def load_faces(self):
        """Загрузка всех лиц из директории"""
        self.known_encodings = []
        self.known_names = []
        
        if not os.path.exists(self.storage_dir):
            return
        
        for filename in os.listdir(self.storage_dir):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                name = os.path.splitext(filename)[0]
                image_path = os.path.join(self.storage_dir, filename)
                image = face_recognition.load_image_file(image_path)
                encodings = face_recognition.face_encodings(image)
                
                if encodings:
                    self.known_encodings.append(encodings[0])
                    self.known_names.append(name)
                    print(f"✓ Загружено лицо: {name}")
        
        print(f"Всего загружено лиц: {len(self.known_names)}")
    
    def save_face(self, face_image, name):
        """Сохранение нового лица"""
        filename = os.path.join(self.storage_dir, f"{name}.jpg")
        cv2.imwrite(filename, face_image)
        print(f"✓ Лицо сохранено как {name}")
        self.load_faces()  # Перезагружаем список
        return True
    
    def get_unique_name(self, base_name):
        """Генерация уникального имени"""
        name = base_name
        counter = 1
        while os.path.exists(os.path.join(self.storage_dir, f"{name}.jpg")):
            name = f"{base_name}_{counter}"
            counter += 1
        return name
    
    def get_count(self):
        """Получение количества известных лиц"""
        return len(self.known_names)
    
    def get_names(self):
        """Получение списка имен"""
        return self.known_names.copy()