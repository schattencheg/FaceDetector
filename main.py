import cv2
import time
from datetime import datetime
import sys
import os

from gui.config_window import ConfigWindow, create_test_image
from utils.text_renderer import TextRenderer
from input.key_handler import KeyHandler
from storage.face_storage import FaceStorage
from core.video_source_factory import VideoSourceFactory
from core.face_detector import FaceDetector
from core.face_recognizer import FaceRecognizer
from core.emotion_analyzer import EmotionAnalyzer
from core.dialog_manager import DialogManager
from core.drawer import Drawer
from core.audio_commands import AudioCommandHandler

class Application:
    """Главный класс приложения с поддержкой голосовых команд"""
    
    def __init__(self, source_config=None, enable_voice=True):
        # Инициализация компонентов
        self.text_renderer = TextRenderer()
        self.key_handler = KeyHandler()
        self.face_storage = FaceStorage("known_faces")
        
        # Создание источника видео из конфигурации
        if source_config is None:
            source_config = {'type': 'screen', 'params': {}}
        
        try:
            self.video_source = VideoSourceFactory.create_from_config(source_config)
        except Exception as e:
            print(f"❌ Ошибка создания источника видео: {e}")
            print("Используем захват экрана по умолчанию")
            self.video_source = VideoSourceFactory.create_from_config({'type': 'screen', 'params': {}})
        
        self.face_detector = FaceDetector()
        self.face_recognizer = FaceRecognizer(self.face_storage)
        self.emotion_analyzer = EmotionAnalyzer()
        self.dialog_manager = DialogManager()
        self.drawer = Drawer(self.text_renderer)
        
        # Аудио система
        self.enable_voice = enable_voice
        self.audio_handler = None
        if enable_voice:
            self.audio_handler = AudioCommandHandler(self)
        
        # Состояния
        self.running = True
        self.screenshot_requested = False
        self.reload_requested = False
        self.face_cooldown = {}
        self.cooldown_duration = 5
        self.voice_learning_active = False
        self.pending_voice_face = None
    
    def run(self):
        """Запуск приложения"""
        self._print_welcome()
        self.key_handler.start()
        
        # Запуск аудио системы
        if self.audio_handler:
            try:
                if not self.audio_handler.start():
                    print("⚠️ Аудио система не активирована (продолжаем без голосовых команд)")
                    self.audio_handler = None
            except Exception as e:
                print(f"⚠️ Ошибка активации аудио: {e}")
                self.audio_handler = None
        
        if not os.path.exists('screenshots'):
            os.makedirs('screenshots')
        
        try:
            while self.running:
                self._handle_commands()
                
                # Получение кадра
                is_paused = (self.dialog_manager.is_open or 
                           self.face_recognizer.is_busy or
                           self.voice_learning_active)
                
                if is_paused:
                    self.video_source.pause()
                    frame = self.video_source.get_last_frame()
                    if frame is None:
                        time.sleep(0.1)
                        continue
                else:
                    self.video_source.resume()
                    try:
                        frame = self.video_source.capture()
                    except StopIteration:
                        print("\n📹 Видео закончилось")
                        break
                
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
                
                # Отображение информации
                self._draw_info_panel(frame)
                
                # Отображение
                cv2.imshow('Система "Свой-Чужой" с обучением', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                time.sleep(0.03)
                
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
        finally:
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
    
    def _draw_info_panel(self, frame):
        """Отрисовка информационной панели"""
        # Информация об источнике
        try:
            source_info = self.video_source.get_info()
            cv2.putText(frame, f"Source: {source_info['type']}", 
                       (frame.shape[1] - 200, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        except:
            pass
        
        # Информация о голосовом управлении
        if self.audio_handler and hasattr(self.audio_handler, 'is_running') and self.audio_handler.is_running:
            cv2.putText(frame, "🎤 Voice: ON", 
                       (frame.shape[1] - 200, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Информация о режиме голосового обучения
        if hasattr(self, 'voice_learning_active') and self.voice_learning_active:
            cv2.putText(frame, "🎤 Скажите имя...", 
                       (frame.shape[1] // 2 - 150, frame.shape[0] - 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    def _handle_commands(self):
        """Обработка клавиатурных команд"""
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
        print("=" * 70)
        print("СИСТЕМА РАСПОЗНАВАНИЯ ЛИЦ С ГОЛОСОВЫМ УПРАВЛЕНИЕМ")
        print("=" * 70)
        
        try:
            source_info = self.video_source.get_info()
            print(f"Источник видео: {source_info['type']}")
        except:
            print(f"Источник видео: {self.video_source.__class__.__name__}")
        
        print("\nУправление:")
        print("  'q' - Выход")
        print("  'l' - Включить/Выключить режим обучения")
        print("  's' - Сохранить скриншот")
        print("  'r' - Перезагрузить базу известных лиц")
        print("  'ENTER' - Добавить лицо в базу (в режиме обучения)")
        
        if self.enable_voice:
            print("\n  Голосовые команды (скажите):")
            print("    'режим обучения' - Переключение режима")
            print("    'сохранить' - Скриншот")
            print("    'перезагрузить' - Перезагрузка базы")
            print("    'добавить' - Добавить лицо")
            print("    'выход' - Выход")
            print("    'информация' - Статус системы")
        
        print("=" * 70)
        
        if self.face_storage.get_count() == 0:
            print("\n⚠️ ВНИМАНИЕ: База лиц пуста!")
            print("   Нажмите 'l' для входа в режим обучения\n")
        else:
            names = ', '.join(self.face_storage.get_names())
            print(f"\n✓ Загружено лиц: {names}\n")
    
    def _cleanup(self):
        """Очистка ресурсов"""
        self.key_handler.stop()
        self.video_source.release()
        if self.audio_handler:
            try:
                self.audio_handler.stop()
            except:
                pass
        cv2.destroyAllWindows()
        print("\nПрограмма завершена.")
    
    # Методы для голосового управления
    def toggle_learning_mode(self):
        """Переключение режима обучения"""
        mode = self.face_recognizer.set_learning_mode(
            not self.face_recognizer.is_learning_mode
        )
        status = "ВКЛЮЧЕН" if mode else "ВЫКЛЮЧЕН"
        print(f"\n🔵 РЕЖИМ ОБУЧЕНИЯ {status} (голосовая команда)")
    
    def take_screenshot(self):
        """Сохранение скриншота"""
        self.screenshot_requested = True
    
    def reload_faces(self):
        """Перезагрузка базы лиц"""
        self.reload_requested = True
        print("🔄 Перезагрузка базы лиц... (голосовая команда)")
    
    def quit(self):
        """Выход из программы"""
        self.running = False
    
    def print_info(self):
        """Вывод информации"""
        try:
            source_info = self.video_source.get_info()
            print(f"\n📊 Информация:")
            print(f"  Источник: {source_info['type']}")
        except:
            print(f"\n📊 Информация:")
            print(f"  Источник: {self.video_source.__class__.__name__}")
        print(f"  Известных лиц: {self.face_storage.get_count()}")
        print(f"  Режим обучения: {'ВКЛ' if self.face_recognizer.is_learning_mode else 'ВЫКЛ'}")
        if self.audio_handler:
            print(f"  Микрофон: {'АКТИВЕН' if self.audio_handler.is_running else 'НЕ АКТИВЕН'}")
    
    def get_face_count(self):
        """Получение количества лиц"""
        return self.face_storage.get_count()
    
    def activate_voice_learning(self):
        """Активация голосового обучения"""
        self.voice_learning_active = True
        print("🎤 Скажите имя для лица...")
    
    def add_new_face_direct(self, face_image, name):
        """Прямое добавление лица"""
        unique_name = self.face_storage.get_unique_name(name)
        self.face_storage.save_face(face_image, unique_name)
        print(f"✓ Добавлено лицо: {unique_name}")
        self.voice_learning_active = False


def main():
    """Главная функция"""
    # Создаем тестовое изображение если его нет
    create_test_image()
    
    # Показываем окно конфигурации
    config_window = ConfigWindow()
    source_config = config_window.show()
    
    # Если пользователь отменил настройку, выходим
    if source_config is None:
        print("Настройка отменена. Выход.")
        return
    
    # Получаем настройки из конфигурации
    enable_voice = config_window.config.get("enable_voice", True)
    
    # Запускаем приложение
    app = Application(source_config, enable_voice)
    app.run()


if __name__ == "__main__":
    main()