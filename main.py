import cv2
import time
from datetime import datetime

from utils.text_renderer import TextRenderer
from input.key_handler import KeyHandler
from storage.face_storage import FaceStorage
from core.video_source import VideoSourceFactory
from core.face_detector import FaceDetector
from core.face_recognizer import FaceRecognizer
from core.emotion_analyzer import EmotionAnalyzer
from core.dialog_manager import DialogManager
from core.drawer import Drawer
from core.audio_commands import AudioCommandHandler

class Application:
    """Главный класс приложения (оркестратор)"""
    
    def __init__(self, source_config):
        # Инициализация всех компонентов
        self.text_renderer = TextRenderer()
        self.key_handler = KeyHandler()
        self.face_storage = FaceStorage("known_faces")

        # Создание источника видео
        if source_config is None:
            source_config = {'type': 'screen', 'params': {}}
        self.video_source = VideoSourceFactory.create_from_config(source_config)

        self.face_detector = FaceDetector()
        self.face_recognizer = FaceRecognizer(self.face_storage)
        self.emotion_analyzer = EmotionAnalyzer()
        self.dialog_manager = DialogManager()
        self.drawer = Drawer(self.text_renderer)
        
        # Состояния
        self.running = True
        self.screenshot_requested = False
        self.reload_requested = False
        
        # Коoldown для добавления лиц
        self.face_cooldown = {}
        self.cooldown_duration = 5
    
    def run(self):
        """Запуск приложения"""
        self._print_welcome()
        self.key_handler.start()
        
        # Создаем директорию для скриншотов
        import os
        if not os.path.exists('screenshots'):
            os.makedirs('screenshots')
        
        while self.running:
            # Обработка глобальных команд
            self._handle_commands()
            
            # Получение кадра
            is_paused = (self.dialog_manager.is_open or self.face_recognizer.is_busy)
            if is_paused:
                self.video_source.pause()
                frame = self.video_source.get_last_frame()
                if frame is None:
                    time.sleep(0.1)
                    continue
            else:
                self.video_source.resume()
                frame = self.video_source.capture()
            
            # Обработка кадра
            frame = self._process_frame(frame, is_paused)
            
            # Сохранение скриншота
            if self.screenshot_requested and not is_paused:
                self._save_screenshot(frame)
                self.screenshot_requested = False
            
            # Перезагрузка базы лиц
            if self.reload_requested:
                self.face_storage.load_faces()
                self.reload_requested = False
            
            # Отображение
            cv2.imshow('Система "Свой-Чужой" с обучением', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            time.sleep(0.03)
        
        self._cleanup()
    
    def _process_frame(self, frame, is_paused):
        """Обработка одного кадра"""
        if is_paused:
            return self.drawer.draw_info_panel(
                frame, 
                self.face_storage.get_count(),
                self.face_recognizer.is_learning_mode,
                is_paused=True
            )
        
        # Обнаружение лиц
        faces = self.face_detector.detect(frame)
        
        if len(faces) == 0:
            return self._draw_ui(frame, [], [])
        
        # Распознавание лиц
        recognized_names = self.face_recognizer.recognize(frame, faces)
        
        # Обработка каждого лица
        for (x, y, w, h), name in zip(faces, recognized_names):
            face_roi = frame[y:y + h, x:x + w]
            
            # Анализ эмоции
            emotion = self.emotion_analyzer.analyze(face_roi)
            
            # Отрисовка лица
            is_highlight = self._should_highlight_face(name, (x, y, w, h))
            frame = self.drawer.draw_face(
                frame, (x, y, w, h), name, emotion,
                self.face_recognizer.is_learning_mode,
                is_highlight
            )
            
            # Обработка добавления нового лица
            if self._should_add_face(name, (x, y, w, h)):
                self._add_new_face(face_roi, (x, y, w, h))
        
        return self._draw_ui(frame, faces, recognized_names)
    
    def _should_highlight_face(self, name, face):
        """Проверка, нужно ли подсвечивать лицо"""
        if name != "Чужой":
            return False
        
        if not self.face_recognizer.is_learning_mode:
            return False
        
        face_id = f"{face[0]}_{face[1]}_{face[2]}_{face[3]}"
        current_time = time.time()
        
        if face_id in self.face_cooldown:
            if current_time - self.face_cooldown[face_id] < self.cooldown_duration:
                return False
        
        return True
    
    def _should_add_face(self, name, face):
        """Проверка, нужно ли добавить лицо"""
        if name != "Чужой":
            return False
        
        if not self.face_recognizer.is_learning_mode:
            return False
        
        if self.dialog_manager.is_open:
            return False
        
        if self.face_recognizer.is_busy:
            return False
        
        if not self.key_handler.is_pressed('enter'):
            return False
        
        face_id = f"{face[0]}_{face[1]}_{face[2]}_{face[3]}"
        current_time = time.time()
        
        if face_id in self.face_cooldown:
            if current_time - self.face_cooldown[face_id] < self.cooldown_duration:
                return False
        
        self.key_handler.consume('enter')
        return True
    
    def _add_new_face(self, face_roi, face):
        """Добавление нового лица"""
        name = self.dialog_manager.show_add_face_dialog(face_roi)
        
        if name:
            unique_name = self.face_recognizer.add_new_face(face_roi, name)
            print(f"✓ Добавлено лицо: {unique_name}")
        
        face_id = f"{face[0]}_{face[1]}_{face[2]}_{face[3]}"
        self.face_cooldown[face_id] = time.time()
    
    def _draw_ui(self, frame, faces, names):
        """Отрисовка пользовательского интерфейса"""
        frame = self.drawer.draw_info_panel(
            frame,
            self.face_storage.get_count(),
            self.face_recognizer.is_learning_mode
        )
        frame = self.drawer.draw_help(frame)
        return frame
    
    def _handle_commands(self):
        """Обработка глобальных команд"""
        if self.key_handler.consume('q'):
            self.running = False
        
        if self.key_handler.consume('l'):
            mode = self.face_recognizer.set_learning_mode(
                not self.face_recognizer.is_learning_mode
            )
            status = "ВКЛЮЧЕН" if mode else "ВЫКЛЮЧЕН"
            print(f"\n🔵 РЕЖИМ ОБУЧЕНИЯ {status}")
        
        if self.key_handler.consume('s'):
            self.screenshot_requested = True
        
        if self.key_handler.consume('r'):
            self.reload_requested = True
            print("🔄 Перезагрузка базы лиц...")
    
    def _save_screenshot(self, frame):
        """Сохранение скриншота"""
        dt = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshots/screenshot_{dt}.jpg"
        success, buffer = cv2.imencode('.jpg', frame)
        if success:
            with open(filename, 'wb') as f:
                f.write(buffer)
            print(f"📸 Скриншот сохранен: {filename}")
    
    def _print_welcome(self):
        """Вывод приветственного сообщения"""
        print("=" * 60)
        print("СИСТЕМА РАСПОЗНАВАНИЯ ЛИЦ С РЕЖИМОМ ОБУЧЕНИЯ")
        print("=" * 60)
        print("Управление:")
        print("  'q' - Выход")
        print("  'l' - Включить/Выключить режим обучения")
        print("  's' - Сохранить скриншот")
        print("  'r' - Перезагрузить базу известных лиц")
        print("  'ENTER' - Добавить лицо в базу (в режиме обучения)")
        print("=" * 60)
        
        if self.face_storage.get_count() == 0:
            print("\n⚠️ ВНИМАНИЕ: База лиц пуста!")
            print("   Нажмите 'l' для входа в режим обучения\n")
        else:
            names = ', '.join(self.face_storage.get_names())
            print(f"\n✓ Загружено лиц: {names}\n")
    
    def _cleanup(self):
        """Очистка ресурсов"""
        self.key_handler.stop()
        cv2.destroyAllWindows()
        print("\nПрограмма завершена.")

def main():
    if False:
        config = None

        """Использование веб-камеры"""
        config = {
            'type': 'webcam',
            'params': {
                'camera_id': 0,
                'width': 640,
                'height': 480
            }
        }

    if False:
        """Использование видеофайла"""
        config = {
            'type': 'video',
            'params': {
                'file_path': 'test_video.mp4',
                'loop': True  # Зациклить видео
            }
        }

    if True:
        """Использование статичного изображения"""
        config = {
            'type': 'image',
            'params': {
                'image_path': 'test_image.jpg'
            }
        }

    if False:
        """Использование скриншотов экрана"""
        config = {
            'type': 'screen',
            'params': {
                'monitor_number': 1,
                'monitor_mode': 'monitor'  # 'monitor', 'primary', 'all'
            }
        }

    app = Application(config)
    app.run()

if __name__ == "__main__":
    main()