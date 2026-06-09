import numpy as np
import cv2
import time
from datetime import datetime
import threading
from queue import Queue
import os
import sys

# Добавляем пути для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.text_renderer import TextRenderer
from input.key_handler import KeyHandler
from storage.face_storage import FaceStorage
from storage.face_manager import FaceManager
from core.video_source_factory import VideoSourceFactory
from core.face_detector import FaceDetector
from core.face_recognizer import FaceRecognizer
from core.emotion_analyzer import EmotionAnalyzer
from core.dialog_manager import DialogManager
from core.drawer import Drawer
from core.audio_commands import AudioCommandHandler


class Application:
    """Главный класс приложения с асинхронной обработкой"""
    
    def __init__(self, source_config=None, enable_voice=True):
        # Инициализация компонентов
        self.text_renderer = TextRenderer()
        self.key_handler = KeyHandler()
        self.face_storage = FaceStorage("known_faces")
        self.face_manager = FaceManager(self.face_storage)
        
        # Создание источника видео
        if source_config is None:
            source_config = {'type': 'screen', 'params': {'max_fps': 10}}
        
        try:
            self.video_source = VideoSourceFactory.create_from_config(source_config)
        except Exception as e:
            print(f"❌ Ошибка создания источника видео: {e}")
            print("Используем захват экрана по умолчанию")
            self.video_source = VideoSourceFactory.create_from_config(
                {'type': 'screen', 'params': {'max_fps': 10}}
            )
        
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
        
        # Очереди для асинхронной обработки
        self.frame_queue = Queue(maxsize=2)
        self.result_queue = Queue(maxsize=2)
        
        # Потоки
        self.processing_thread = None
        self.display_thread = None
        self.is_running = False
        
        # Состояния
        self.screenshot_requested = False
        self.reload_requested = False
        self.face_cooldown = {}
        self.cooldown_duration = 2
        self.voice_learning_active = False
        self.current_frame = None
        self.last_process_time = 0
        self.process_interval = 0.1
        
        # Флаг для предотвращения множественных вызовов
        self.last_learning_toggle = 0
        self.learning_toggle_cooldown = 0.5
    
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
        
        # Запуск потока обработки
        self.is_running = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        
        # Создаем директорию для скриншотов
        if not os.path.exists('screenshots'):
            os.makedirs('screenshots')
        
        try:
            # Основной цикл отображения
            while self.is_running:
                self._handle_commands()
                
                # Получаем обработанный кадр из очереди
                try:
                    display_frame = self.result_queue.get_nowait()
                    self.current_frame = display_frame
                except:
                    pass
                
                # Показываем последний обработанный кадр
                if self.current_frame is not None:
                    cv2.imshow('Система "Свой-Чужой" с обучением', self.current_frame)
                
                # Сохранение скриншота
                if self.screenshot_requested and self.current_frame is not None:
                    self._save_screenshot(self.current_frame)
                    self.screenshot_requested = False
                
                # Перезагрузка базы лиц
                if self.reload_requested:
                    self.face_storage.load_faces()
                    self.reload_requested = False
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('m'):
                    self._open_face_manager()
                
                time.sleep(0.01)
                
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._cleanup()
    
    def _processing_loop(self):
        """Поток обработки кадров"""
        while self.is_running:
            try:
                current_time = time.time()
                
                # Ограничиваем частоту обработки
                if current_time - self.last_process_time >= self.process_interval:
                    # Получаем свежий кадр из источника
                    frame = self.video_source.capture()
                    
                    if frame is not None:
                        # Обрабатываем кадр
                        processed_frame = self._process_frame(frame)
                        
                        # Отправляем в очередь результатов
                        if self.result_queue.full():
                            try:
                                self.result_queue.get_nowait()
                            except:
                                pass
                        self.result_queue.put(processed_frame)
                        
                        self.last_process_time = current_time
                else:
                    time.sleep(0.005)
                    
            except StopIteration:
                print("\n📹 Видео закончилось")
                self.is_running = False
                break
            except Exception as e:
                print(f"Ошибка в потоке обработки: {e}")
                time.sleep(0.1)
    
    def _process_frame(self, frame):
        """Обработка одного кадра"""
        is_paused = (self.dialog_manager.is_open or 
                    self.face_recognizer.is_busy or
                    self.voice_learning_active)
        
        if is_paused:
            return self.drawer.draw_info_panel(
                frame.copy(),
                self.face_storage.get_count(),
                self.face_recognizer.is_learning(),
                is_paused=True
            )
        
        # ИСПОЛЬЗУЕМ ТОЛЬКО face_recognition
        face_locations, recognized_names = self.face_recognizer.detect_and_recognize(frame)
        
        if len(face_locations) == 0:
            return self._draw_ui(frame.copy(), [], [])
        
        # Конвертируем (top, right, bottom, left) в (x, y, w, h)
        faces = []
        for (top, right, bottom, left) in face_locations:
            x = left
            y = top
            w = right - left
            h = bottom - top
            faces.append((x, y, w, h))
        
        # Обработка каждого лица
        for (x, y, w, h), name in zip(faces, recognized_names):
            face_roi = frame[y:y + h, x:x + w]
            
            # Анализ эмоции
            emotion = self.emotion_analyzer.analyze(face_roi)
            
            # Отрисовка
            is_highlight = self._should_highlight_face(name, (x, y, w, h))
            frame = self.drawer.draw_face(
                frame, (x, y, w, h), name, emotion,
                self.face_recognizer.is_learning(),
                is_highlight
            )
            
            # Подсказка
            if self.face_recognizer.is_learning() and name == "Чужой":
                frame = self.text_renderer.draw_text(
                    frame, "НАЖМИТЕ ENTER", 
                    (x, y - 50), 16, (0, 255, 255)
                )
            
            # Добавление лица
            if self._should_add_face(name, (x, y, w, h), face_roi):
                print(f"🎯 Добавляем лицо в позиции ({x}, {y})")
                self._add_new_face_async(face_roi)
        
        return self._draw_ui(frame, faces, recognized_names)
    
    def _should_highlight_face(self, name, face):
        """Проверка, нужно ли подсвечивать лицо"""
        if name != "Чужой":
            return False
        
        if not self.face_recognizer.is_learning():
            return False
        
        face_id = f"{face[0]}_{face[1]}_{face[2]}_{face[3]}"
        current_time = time.time()
        
        if face_id in self.face_cooldown:
            if current_time - self.face_cooldown[face_id] < self.cooldown_duration:
                return False        
        return True
    
    def _should_add_face(self, name, face, face_roi):
        """Проверка, нужно ли добавить лицо"""
        if name != "Чужой":
            return False
        
        if not self.face_recognizer.is_learning():
            return False
        
        if self.dialog_manager.is_open:
            return False
        
        if self.face_recognizer.is_busy:
            return False
        
        if not self.key_handler.is_pressed('enter'):
            return False
        
        # Создаем уникальный хеш на основе изображения лица
        face_hash = hash(face_roi.tobytes())
        current_time = time.time()
        
        if face_hash in self.face_cooldown:
            if current_time - self.face_cooldown[face_hash] < self.cooldown_duration:
                print(f"⏱️ Это лицо уже добавлялось")
                self.key_handler.consume('enter')
                return False
        
        self.key_handler.consume('enter')
        self.face_cooldown[face_hash] = current_time
        return True

    def _add_new_face_async(self, face_roi):
        """Асинхронное добавление нового лица"""
        def add_face():
            name = self.dialog_manager.show_add_face_dialog(face_roi)
            if name:
                unique_name = self.face_recognizer.add_new_face(face_roi, name)
                print(f"✓ Добавлено лицо: {unique_name}")
            else:
                print(f"❌ Добавление отменено")
        
        thread = threading.Thread(target=add_face, daemon=True)
        thread.start()
    
    def _draw_ui(self, frame, faces, names):
        """Отрисовка пользовательского интерфейса"""
        frame = self.drawer.draw_info_panel(
            frame,
            self.face_storage.get_count(),
            self.face_recognizer.is_learning()
        )
        frame = self.drawer.draw_help(frame)
        
        # Информация об источнике
        try:
            source_info = self.video_source.get_info()
            fps_text = f"{source_info.get('max_fps', '?')} FPS"
            self.text_renderer.draw_text(frame, f"Source: {source_info['type']} ({fps_text})", 
                       (frame.shape[1] - 250, 30), 
                       16, (255, 255, 255))
        except:
            pass
        
        # Информация о голосовом управлении
        if self.audio_handler and hasattr(self.audio_handler, 'is_running') and self.audio_handler.is_running:
            self.text_renderer.draw_text(frame, "🎤 Voice: ON", 
                       (frame.shape[1] - 200, 60), 
                       16, (0, 255, 0))
        
        # Информация о режиме голосового обучения
        if self.voice_learning_active:
            self.text_renderer.draw_text(frame, "🎤 Скажите имя...", 
                       (frame.shape[1] // 2 - 150, frame.shape[0] - 50), 
                       16, (0, 255, 255))
        
        # Подсказка о меню управления
        self.text_renderer.draw_text(frame, "Press 'm' - Manage faces", 
                   (10, frame.shape[0] - 10), 
                   16, (200, 200, 200))
        
        return frame
    
    def _handle_commands(self):
        """Обработка клавиатурных команд"""
        
        if self.key_handler.consume('q'):
            self.is_running = False
            return
        
        if self.key_handler.consume('l'):
            current_time = time.time()
            
            if current_time - self.last_learning_toggle > self.learning_toggle_cooldown:
                self.last_learning_toggle = current_time
                
                # ПРЯМОЕ ПЕРЕКЛЮЧЕНИЕ
                if self.face_recognizer.is_learning():
                    self.face_recognizer.set_learning_mode(False)
                    print(f"\n🔴 РЕЖИМ ОБУЧЕНИЯ ВЫКЛЮЧЕН\n")
                else:
                    self.face_recognizer.set_learning_mode(True)
                    print(f"\n🟢 РЕЖИМ ОБУЧЕНИЯ ВКЛЮЧЕН")
                    print(f"   Наведитесь на лицо и нажмите ENTER\n")
        
        if self.key_handler.consume('s'):
            self.screenshot_requested = True
        
        if self.key_handler.consume('r'):
            self.reload_requested = True
    def _open_face_manager(self):
        """Открытие менеджера лиц"""
        try:
            from gui.face_manager_window import FaceManagerWindow
            # Запускаем в отдельном потоке, чтобы не блокировать основное окно
            def open_manager():
                manager = FaceManagerWindow(self.face_manager)
                manager.show()
                # После закрытия менеджера обновляем базу
                self.face_storage.load_faces()
            
            thread = threading.Thread(target=open_manager, daemon=True)
            thread.start()
        except Exception as e:
            print(f"Ошибка открытия менеджера лиц: {e}")
    
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
        print("СИСТЕМА РАСПОЗНАВАНИЯ ЛИЦ (АСИНХРОННАЯ ОБРАБОТКА)")
        print("=" * 70)
        
        try:
            source_info = self.video_source.get_info()
            print(f"Источник видео: {source_info['type']}")
            print(f"FPS ограничение: {source_info.get('max_fps', '?')}")
        except:
            print(f"Источник видео: {self.video_source.__class__.__name__}")
        
        print("\nУправление (мгновенный отклик):")
        print("  'q' - Выход")
        print("  'l' - Включить/Выключить режим обучения")
        print("  's' - Сохранить скриншот")
        print("  'r' - Перезагрузить базу известных лиц")
        print("  'm' - Открыть менеджер лиц (переименование/удаление)")
        print("  'ENTER' - Добавить лицо в базу (в режиме обучения)")
        
        if self.enable_voice:
            print("\n  Голосовые команды:")
            print("    'режим обучения' - Переключение режима")
            print("    'сохранить' - Скриншот")
            print("    'перезагрузить' - Перезагрузка базы")
            print("    'добавить' - Добавить лицо")
            print("    'менеджер лиц' - Открыть менеджер")
            print("    'выход' - Выход")
        
        print("=" * 70)
        
        if self.face_storage.get_count() == 0:
            print("\n⚠️ ВНИМАНИЕ: База лиц пуста!")
            print("   Нажмите 'l' для входа в режим обучения")
            print("   Затем наведитесь на лицо и нажмите ENTER\n")
        else:
            names = ', '.join(self.face_storage.get_names())
            print(f"\n✓ Загружено лиц: {names}\n")
    
    def _cleanup(self):
        """Очистка ресурсов"""
        self.is_running = False
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
        current_time = time.time()
        if current_time - getattr(self, '_last_voice_toggle', 0) > 0.5:
            self._last_voice_toggle = current_time
            new_mode = not self.face_recognizer.is_learning()
            self.face_recognizer.set_learning_mode(new_mode)
            status = "ВКЛЮЧЕН" if new_mode else "ВЫКЛЮЧЕН"
            print(f"\n🔵 РЕЖИМ ОБУЧЕНИЯ {status} (голосовая команда)")
    
    def take_screenshot(self):
        self.screenshot_requested = True
    
    def reload_faces(self):
        self.reload_requested = True
    
    def quit(self):
        self.is_running = False
    
    def print_info(self):
        try:
            source_info = self.video_source.get_info()
            print(f"\n📊 Статус:")
            print(f"  Источник: {source_info['type']}")
            print(f"  FPS: {source_info.get('max_fps', '?')}")
        except:
            pass
        print(f"  Известных лиц: {self.face_storage.get_count()}")
        print(f"  Режим обучения: {'ВКЛ' if self.face_recognizer.is_learning() else 'ВЫКЛ'}")
    
    def get_face_count(self):
        return self.face_storage.get_count()
    
    def activate_voice_learning(self):
        self.voice_learning_active = True
    
    def add_new_face_direct(self, face_image, name):
        unique_name = self.face_storage.get_unique_name(name)
        self.face_storage.save_face(face_image, unique_name)
        print(f"✓ Добавлено лицо: {unique_name}")
        self.voice_learning_active = False
    
    def open_face_manager(self):
        """Открытие менеджера лиц (голосовая команда)"""
        self._open_face_manager()


def create_test_image():
    """Создание тестового изображения если его нет"""
    if not os.path.exists("test_image.jpg"):
        import numpy as np
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.imwrite("test_image.jpg", test_image)
        print("✓ Создано тестовое изображение: test_image.jpg")


def main():
    """Главная функция запуска"""
    # Создаем тестовое изображение если его нет
    create_test_image()
    
    # Пытаемся импортировать GUI конфигурации
    try:
        from gui.config_window import ConfigWindow
        
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
        
    except ImportError as e:
        print(f"⚠️ Модуль GUI не найден: {e}")
        print("Запуск с параметрами по умолчанию...")
        
        # Если GUI не доступен, запускаем с параметрами командной строки
        source_config = None
        enable_voice = True
        
        if len(sys.argv) > 1:
            source_type = sys.argv[1]
            
            if source_type == 'webcam':
                source_config = {'type': 'webcam', 'params': {'max_fps': 15}}
            elif source_type == 'video' and len(sys.argv) > 2:
                source_config = {
                    'type': 'video',
                    'params': {
                        'file_path': sys.argv[2],
                        'loop': '--loop' in sys.argv,
                        'max_fps': 15
                    }
                }
            elif source_type == 'image' and len(sys.argv) > 2:
                source_config = {
                    'type': 'image',
                    'params': {
                        'image_path': sys.argv[2],
                        'max_fps': 5
                    }
                }
            elif source_type == 'screen':
                source_config = {'type': 'screen', 'params': {'max_fps': 10}}
            
            if '--no-voice' in sys.argv:
                enable_voice = False
        
        if source_config is None:
            source_config = {'type': 'screen', 'params': {'max_fps': 10}}
        
        app = Application(source_config, enable_voice)
        app.run()


if __name__ == "__main__":
    main()
