import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
from pathlib import Path

class SettingsDialog:
    """Диалоговое окно для выбора источника видео и настроек"""
    
    SETTINGS_FILE = "app_settings.json"
    
    def __init__(self):
        self.root = None
        self.result = None
        self.settings = self.load_settings()
        
    def load_settings(self):
        """Загрузка сохраненных настроек"""
        default_settings = {
            'last_source_type': 'screen',
            'webcam': {'camera_id': 0, 'width': 640, 'height': 480},
            'video': {'file_path': '', 'loop': False},
            'image': {'file_path': 'test_image.jpg'},
            'screen': {'monitor_number': 1, 'monitor_mode': 'monitor'},
            'microphone_enabled': True,
            'recent_files': {
                'video': [],
                'image': []
            }
        }
        
        if os.path.exists(self.SETTINGS_FILE):
            try:
                with open(self.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    # Объединяем с дефолтными настройками
                    for key in default_settings:
                        if key not in saved:
                            saved[key] = default_settings[key]
                    return saved
            except Exception as e:
                print(f"Ошибка загрузки настроек: {e}")
        
        # Создаем test_image.jpg если его нет
        self._create_default_image()
        
        return default_settings
    
    def save_settings(self):
        """Сохранение настроек"""
        try:
            with open(self.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
            return False
    
    def _create_default_image(self):
        """Создание тестового изображения по умолчанию"""
        if not os.path.exists('test_image.jpg'):
            try:
                import cv2
                import numpy as np
                # Создаем тестовое изображение с текстом
                img = np.ones((480, 640, 3), dtype=np.uint8) * 255
                cv2.putText(img, "Test Image", (200, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
                cv2.imwrite('test_image.jpg', img)
                print("✓ Создано тестовое изображение: test_image.jpg")
            except:
                pass
    
    def show(self):
        """Показ диалогового окна"""
        self.root = tk.Tk()
        self.root.title("Настройки распознавания лиц")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Центрируем окно
        self.root.eval('tk::PlaceWindow . center')
        
        # Стили
        style = ttk.Style()
        style.theme_use('clam')
        
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Настройка источника видео", 
                                font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Выбор типа источника
        ttk.Label(main_frame, text="Тип источника:", font=('Arial', 11)).grid(
            row=1, column=0, sticky=tk.W, pady=5)
        
        self.source_type = tk.StringVar(value=self.settings['last_source_type'])
        source_types = [
            ('Захват экрана', 'screen'),
            ('Веб-камера', 'webcam'),
            ('Видеофайл', 'video'),
            ('Изображение', 'image')
        ]
        
        self.source_frame = ttk.Frame(main_frame)
        self.source_frame.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        for i, (text, value) in enumerate(source_types):
            ttk.Radiobutton(self.source_frame, text=text, variable=self.source_type,
                           value=value, command=self.on_source_change).grid(
                row=0, column=i, padx=5)
        
        # Рамка для динамических настроек
        self.dynamic_frame = ttk.LabelFrame(main_frame, text="Настройки источника", padding="10")
        self.dynamic_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=20)
        
        # Настройки микрофона
        mic_frame = ttk.LabelFrame(main_frame, text="Аудио", padding="10")
        mic_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.microphone_enabled = tk.BooleanVar(value=self.settings['microphone_enabled'])
        ttk.Checkbutton(mic_frame, text="Включить микрофон для голосового управления",
                       variable=self.microphone_enabled).grid(row=0, column=0, sticky=tk.W)
        
        ttk.Label(mic_frame, text="Поддерживаемые команды: 'режим обучения', 'сохранить', 'выход' и др.",
                 font=('Arial', 9), foreground='gray').grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Запустить", command=self.on_ok, 
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.on_cancel, 
                  width=15).pack(side=tk.LEFT, padx=5)
        
        # Инициализация динамических настроек
        self.on_source_change()
        
        # Устанавливаем фокус
        self.root.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.root.bind('<Return>', lambda e: self.on_ok())
        
        self.root.mainloop()
        return self.result
    
    def on_source_change(self):
        """Обработка изменения типа источника"""
        # Очищаем динамический фрейм
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()
        
        source = self.source_type.get()
        
        if source == 'screen':
            self._create_screen_settings()
        elif source == 'webcam':
            self._create_webcam_settings()
        elif source == 'video':
            self._create_video_settings()
        elif source == 'image':
            self._create_image_settings()
    
    def _create_screen_settings(self):
        """Настройки захвата экрана"""
        ttk.Label(self.dynamic_frame, text="Монитор:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.monitor_number = tk.IntVar(value=self.settings['screen']['monitor_number'])
        monitor_spin = ttk.Spinbox(self.dynamic_frame, from_=1, to=4, 
                                   width=10, textvariable=self.monitor_number)
        monitor_spin.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(self.dynamic_frame, text="Режим:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.monitor_mode = tk.StringVar(value=self.settings['screen']['monitor_mode'])
        ttk.Radiobutton(self.dynamic_frame, text="Конкретный монитор", 
                       variable=self.monitor_mode, value="monitor").grid(row=1, column=1, sticky=tk.W)
        ttk.Radiobutton(self.dynamic_frame, text="Главный монитор", 
                       variable=self.monitor_mode, value="primary").grid(row=2, column=1, sticky=tk.W)
        ttk.Radiobutton(self.dynamic_frame, text="Все мониторы", 
                       variable=self.monitor_mode, value="all").grid(row=3, column=1, sticky=tk.W)
    
    def _create_webcam_settings(self):
        """Настройки веб-камеры"""
        ttk.Label(self.dynamic_frame, text="ID камеры:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.camera_id = tk.IntVar(value=self.settings['webcam']['camera_id'])
        camera_spin = ttk.Spinbox(self.dynamic_frame, from_=0, to=10, 
                                  width=10, textvariable=self.camera_id)
        camera_spin.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(self.dynamic_frame, text="Разрешение:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        resolution_frame = ttk.Frame(self.dynamic_frame)
        resolution_frame.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        self.webcam_width = tk.IntVar(value=self.settings['webcam']['width'])
        self.webcam_height = tk.IntVar(value=self.settings['webcam']['height'])
        
        ttk.Spinbox(resolution_frame, from_=320, to=1920, step=160,
                   width=8, textvariable=self.webcam_width).pack(side=tk.LEFT)
        ttk.Label(resolution_frame, text="x").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(resolution_frame, from_=240, to=1080, step=120,
                   width=8, textvariable=self.webcam_height).pack(side=tk.LEFT)
    
    def _create_video_settings(self):
        """Настройки видеофайла"""
        ttk.Label(self.dynamic_frame, text="Файл видео:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.video_path = tk.StringVar(value=self.settings['video']['file_path'])
        
        path_frame = ttk.Frame(self.dynamic_frame)
        path_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        self.video_entry = ttk.Entry(path_frame, textvariable=self.video_path, width=40)
        self.video_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(path_frame, text="Обзор...", command=self.browse_video_file).pack(side=tk.LEFT, padx=5)
        
        # Список последних видео
        if self.settings['recent_files']['video']:
            ttk.Label(self.dynamic_frame, text="Недавние:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
            
            recent_frame = ttk.Frame(self.dynamic_frame)
            recent_frame.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
            
            for video_path in self.settings['recent_files']['video'][:3]:
                ttk.Button(recent_frame, text=os.path.basename(video_path),
                          command=lambda p=video_path: self.video_path.set(p),
                          width=30).pack(anchor=tk.W, pady=2)
        
        self.video_loop = tk.BooleanVar(value=self.settings['video']['loop'])
        ttk.Checkbutton(self.dynamic_frame, text="Зациклить воспроизведение",
                       variable=self.video_loop).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=10)
    
    def _create_image_settings(self):
        """Настройки изображения"""
        ttk.Label(self.dynamic_frame, text="Файл изображения:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.image_path = tk.StringVar(value=self.settings['image']['file_path'])
        
        path_frame = ttk.Frame(self.dynamic_frame)
        path_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        self.image_entry = ttk.Entry(path_frame, textvariable=self.image_path, width=40)
        self.image_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(path_frame, text="Обзор...", command=self.browse_image_file).pack(side=tk.LEFT, padx=5)
        
        # Список последних изображений
        if self.settings['recent_files']['image']:
            ttk.Label(self.dynamic_frame, text="Недавние:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
            
            recent_frame = ttk.Frame(self.dynamic_frame)
            recent_frame.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
            
            for image_path in self.settings['recent_files']['image'][:3]:
                ttk.Button(recent_frame, text=os.path.basename(image_path),
                          command=lambda p=image_path: self.image_path.set(p),
                          width=30).pack(anchor=tk.W, pady=2)
    
    def browse_video_file(self):
        """Выбор видеофайла"""
        file_path = filedialog.askopenfilename(
            title="Выберите видеофайл",
            filetypes=[
                ("Видео файлы", "*.mp4 *.avi *.mov *.mkv *.flv"),
                ("Все файлы", "*.*")
            ]
        )
        if file_path:
            self.video_path.set(file_path)
            self._add_to_recent('video', file_path)
    
    def browse_image_file(self):
        """Выбор изображения"""
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[
                ("Изображения", "*.jpg *.jpeg *.png *.bmp *.tiff"),
                ("Все файлы", "*.*")
            ]
        )
        if file_path:
            self.image_path.set(file_path)
            self._add_to_recent('image', file_path)
    
    def _add_to_recent(self, file_type, file_path):
        """Добавление файла в список недавних"""
        recent = self.settings['recent_files'][file_type]
        if file_path in recent:
            recent.remove(file_path)
        recent.insert(0, file_path)
        self.settings['recent_files'][file_type] = recent[:5]  # Оставляем 5 последних
    
    def on_ok(self):
        """Подтверждение настроек"""
        source = self.source_type.get()
        
        # Сохраняем настройки
        self.settings['last_source_type'] = source
        self.settings['microphone_enabled'] = self.microphone_enabled.get()
        
        # Формируем конфигурацию
        config = {'type': source, 'params': {}}
        
        if source == 'screen':
            config['params'] = {
                'monitor_number': self.monitor_number.get(),
                'monitor_mode': self.monitor_mode.get()
            }
            self.settings['screen'] = config['params']
            
        elif source == 'webcam':
            config['params'] = {
                'camera_id': self.camera_id.get(),
                'width': self.webcam_width.get(),
                'height': self.webcam_height.get()
            }
            self.settings['webcam'] = config['params']
            
        elif source == 'video':
            video_path = self.video_path.get().strip()
            if not video_path:
                messagebox.showerror("Ошибка", "Выберите видеофайл!")
                return
            if not os.path.exists(video_path):
                messagebox.showerror("Ошибка", f"Файл не найден: {video_path}")
                return
            
            config['params'] = {
                'file_path': video_path,
                'loop': self.video_loop.get()
            }
            self.settings['video'] = {
                'file_path': video_path,
                'loop': self.video_loop.get()
            }
            
        elif source == 'image':
            image_path = self.image_path.get().strip()
            if not image_path:
                messagebox.showerror("Ошибка", "Выберите изображение!")
                return
            if not os.path.exists(image_path):
                messagebox.showerror("Ошибка", f"Файл не найден: {image_path}")
                return
            
            config['params'] = {'image_path': image_path}
            self.settings['image'] = {'file_path': image_path}
        
        # Сохраняем настройки
        self.save_settings()
        
        self.result = {
            'config': config,
            'microphone_enabled': self.microphone_enabled.get()
        }
        self.root.destroy()
    
    def on_cancel(self):
        """Отмена"""
        self.result = None
        self.root.destroy()


def show_settings_dialog():
    """Показать диалог настроек и вернуть конфигурацию"""
    dialog = SettingsDialog()
    return dialog.show()