import os
import cv2
import shutil
from datetime import datetime

class FaceManager:
    """Класс для управления базой лиц (переименование, удаление, список)"""
    
    def __init__(self, face_storage):
        self.face_storage = face_storage
    
    def list_faces(self):
        """Получить список всех лиц"""
        return list(zip(self.face_storage.known_names, self.face_storage.known_encodings))
    
    def rename_face(self, old_name, new_name):
        """Переименовать лицо"""
        if old_name not in self.face_storage.known_names:
            return False, f"Лицо '{old_name}' не найдено"
        
        if new_name in self.face_storage.known_names:
            return False, f"Имя '{new_name}' уже существует"
        
        # Переименовываем файл
        old_path = os.path.join(self.face_storage.storage_dir, f"{old_name}.jpg")
        new_path = os.path.join(self.face_storage.storage_dir, f"{new_name}.jpg")
        
        try:
            os.rename(old_path, new_path)
            self.face_storage.load_faces()  # Перезагружаем базу
            return True, f"Лицо переименовано: {old_name} -> {new_name}"
        except Exception as e:
            return False, f"Ошибка переименования: {e}"
    
    def delete_face(self, name):
        """Удалить лицо из базы"""
        if name not in self.face_storage.known_names:
            return False, f"Лицо '{name}' не найдено"
        
        file_path = os.path.join(self.face_storage.storage_dir, f"{name}.jpg")
        
        try:
            # Перемещаем в папку удаленных (на всякий случай)
            deleted_dir = os.path.join(self.face_storage.storage_dir, "deleted")
            if not os.path.exists(deleted_dir):
                os.makedirs(deleted_dir)
            
            backup_name = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            backup_path = os.path.join(deleted_dir, backup_name)
            shutil.move(file_path, backup_path)
            
            self.face_storage.load_faces()  # Перезагружаем базу
            return True, f"Лицо '{name}' удалено"
        except Exception as e:
            return False, f"Ошибка удаления: {e}"
    
    def get_face_image(self, name):
        """Получить изображение лица по имени"""
        if name not in self.face_storage.known_names:
            return None
        
        file_path = os.path.join(self.face_storage.storage_dir, f"{name}.jpg")
        if os.path.exists(file_path):
            return cv2.imread(file_path)
        return None