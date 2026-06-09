import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
from pathlib import Path

class ConfigWindow:
    """Окно начальной конфигурации приложения"""
    
    DEFAULT_CONFIG = {
        "last_selected_option": "screen",
        "video_path": "",
        "image_path": "test_image.jpg",
        "enable_voice": True,
        "monitor_number": 1,
        "camera_id": 0,
        "webcam_width": 640,
        "webcam_height": 480,
        "video_loop": False
    }
    
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.root = None
        self.result = None
        
    def load_config(self):
        """Загрузка конфигурации из файла"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Заполняем отсутствующие ключи значениями по умолчанию
                    for key, value in self.DEFAULT_CONFIG.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                print(f"Ошибка загрузки конфигурации: {e}")
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """Сохранение конфигурации в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
            return False
    
    def show(self):
        """Отображение окна конфигурации"""
        self.root = tk.Tk()
        self.root.title("Настройка системы распознавания")
        self.root.geometry("600x550")
        self.root.configure(bg='#2b2b2b')
        
        # Центрируем окно
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.root.winfo_screenheight() // 2) - (550 // 2)
        self.root.geometry(f"600x550+{x}+{y}")
        
        # Делаем окно поверх всех
        self.root.attributes('-topmost', True)
        
        # Заголовок
        title_label = tk.Label(
            self.root,
            text="Настройка системы распознавания лиц",
            font=('Arial', 16, 'bold'),
            fg='white',
            bg='#2b2b2b'
        )
        title_label.pack(pady=20)
        
        # Основной фрейм
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill='both', expand=True, padx=30)
        
        # 1. Выбор источника видео
        source_frame = tk.LabelFrame(
            main_frame,
            text="Источник видео",
            font=('Arial', 12, 'bold'),
            fg='white',
            bg='#2b2b2b',
            bd=2,
            relief='groove'
        )
        source_frame.pack(fill='x', pady=10)
        
        # Радиокнопки для выбора источника
        self.source_var = tk.StringVar(value=self.config.get("last_selected_option", "screen"))
        
        sources = [
            ("Захват экрана", "screen"),
            ("Веб-камера", "webcam"),
            ("Видеофайл", "video"),
            ("Изображение", "image")
        ]
        
        for text, value in sources:
            rb = tk.Radiobutton(
                source_frame,
                text=text,
                variable=self.source_var,
                value=value,
                font=('Arial', 11),
                fg='white',
                bg='#2b2b2b',
                selectcolor='#2b2b2b',
                command=self.on_source_change
            )
            rb.pack(anchor='w', padx=20, pady=5)
        
        # 2. Фрейм для дополнительных параметров (зависит от выбранного источника)
        self.params_frame = tk.LabelFrame(
            main_frame,
            text="Параметры",
            font=('Arial', 12, 'bold'),
            fg='white',
            bg='#2b2b2b',
            bd=2,
            relief='groove'
        )
        self.params_frame.pack(fill='x', pady=10)
        
        # Контейнер для динамических параметров
        self.dynamic_frame = tk.Frame(self.params_frame, bg='#2b2b2b')
        self.dynamic_frame.pack(fill='x', padx=10, pady=10)
        
        # 3. Настройки микрофона
        voice_frame = tk.LabelFrame(
            main_frame,
            text="Аудио",
            font=('Arial', 12, 'bold'),
            fg='white',
            bg='#2b2b2b',
            bd=2,
            relief='groove'
        )
        voice_frame.pack(fill='x', pady=10)
        
        self.voice_var = tk.BooleanVar(value=self.config.get("enable_voice", True))
        voice_check = tk.Checkbutton(
            voice_frame,
            text="Включить голосовое управление",
            variable=self.voice_var,
            font=('Arial', 11),
            fg='white',
            bg='#2b2b2b',
            selectcolor='#2b2b2b'
        )
        voice_check.pack(anchor='w', padx=20, pady=10)
        
        # 4. Кнопки управления
        button_frame = tk.Frame(main_frame, bg='#2b2b2b')
        button_frame.pack(fill='x', pady=20)
        
        ok_button = tk.Button(
            button_frame,
            text="Запустить",
            command=self.on_ok,
            font=('Arial', 12, 'bold'),
            bg='#4CAF50',
            fg='white',
            padx=30,
            pady=8
        )
        ok_button.pack(side='left', padx=10)
        
        cancel_button = tk.Button(
            button_frame,
            text="Отмена",
            command=self.on_cancel,
            font=('Arial', 12),
            bg='#f44336',
            fg='white',
            padx=30,
            pady=8
        )
        cancel_button.pack(side='left', padx=10)
        
        # Инициализируем отображение параметров
        self.on_source_change()
        
        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
        # Запускаем главный цикл
        self.root.mainloop()
        
        return self.result
    
    def on_source_change(self):
        """Обработка изменения источника видео"""
        # Очищаем динамический фрейм
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()
        
        source = self.source_var.get()
        
        if source == "screen":
            self._create_screen_params()
        elif source == "webcam":
            self._create_webcam_params()
        elif source == "video":
            self._create_video_params()
        elif source == "image":
            self._create_image_params()
    
    def _create_screen_params(self):
        """Параметры для захвата экрана"""
        tk.Label(
            self.dynamic_frame,
            text="Номер монитора:",
            font=('Arial', 10),
            fg='white',
            bg='#2b2b2b'
        ).grid(row=0, column=0, sticky='w', pady=5)
        
        self.monitor_var = tk.IntVar(value=self.config.get("monitor_number", 1))
        monitor_spin = tk.Spinbox(
            self.dynamic_frame,
            from_=1,
            to=4,
            textvariable=self.monitor_var,
            width=10,
            font=('Arial', 10)
        )
        monitor_spin.grid(row=0, column=1, sticky='w', pady=5, padx=10)
        
        tk.Label(
            self.dynamic_frame,
            text="(1 - основной монитор, 2,3,4 - дополнительные)",
            font=('Arial', 9),
            fg='gray',
            bg='#2b2b2b'
        ).grid(row=0, column=2, sticky='w', pady=5, padx=10)
    
    def _create_webcam_params(self):
        """Параметры для веб-камеры"""
        # ID камеры
        tk.Label(
            self.dynamic_frame,
            text="ID камеры:",
            font=('Arial', 10),
            fg='white',
            bg='#2b2b2b'
        ).grid(row=0, column=0, sticky='w', pady=5)
        
        self.camera_id_var = tk.IntVar(value=self.config.get("camera_id", 0))
        camera_spin = tk.Spinbox(
            self.dynamic_frame,
            from_=0,
            to=10,
            textvariable=self.camera_id_var,
            width=10,
            font=('Arial', 10)
        )
        camera_spin.grid(row=0, column=1, sticky='w', pady=5, padx=10)
        
        # Разрешение
        tk.Label(
            self.dynamic_frame,
            text="Разрешение:",
            font=('Arial', 10),
            fg='white',
            bg='#2b2b2b'
        ).grid(row=1, column=0, sticky='w', pady=5)
        
        resolutions_frame = tk.Frame(self.dynamic_frame, bg='#2b2b2b')
        resolutions_frame.grid(row=1, column=1, columnspan=2, sticky='w', pady=5, padx=10)
        
        self.webcam_width_var = tk.IntVar(value=self.config.get("webcam_width", 640))
        self.webcam_height_var = tk.IntVar(value=self.config.get("webcam_height", 480))
        
        width_entry = tk.Spinbox(
            resolutions_frame,
            from_=320,
            to=1920,
            increment=160,
            textvariable=self.webcam_width_var,
            width=8,
            font=('Arial', 10)
        )
        width_entry.pack(side='left')
        
        tk.Label(resolutions_frame, text="x", font=('Arial', 10), fg='white', bg='#2b2b2b').pack(side='left', padx=5)
        
        height_entry = tk.Spinbox(
            resolutions_frame,
            from_=240,
            to=1080,
            increment=120,
            textvariable=self.webcam_height_var,
            width=8,
            font=('Arial', 10)
        )
        height_entry.pack(side='left')
    
    def _create_video_params(self):
        """Параметры для видеофайла"""
        # Путь к файлу
        tk.Label(
            self.dynamic_frame,
            text="Путь к видеофайлу:",
            font=('Arial', 10),
            fg='white',
            bg='#2b2b2b'
        ).grid(row=0, column=0, sticky='w', pady=5)
        
        self.video_path_var = tk.StringVar(value=self.config.get("video_path", ""))
        
        path_entry = tk.Entry(
            self.dynamic_frame,
            textvariable=self.video_path_var,
            width=40,
            font=('Arial', 10)
        )
        path_entry.grid(row=0, column=1, sticky='w', pady=5, padx=10)
        
        browse_button = tk.Button(
            self.dynamic_frame,
            text="Обзор...",
            command=self.browse_video,
            font=('Arial', 9),
            bg='#555555',
            fg='white'
        )
        browse_button.grid(row=0, column=2, sticky='w', pady=5, padx=5)
        
        # Зацикливание
        self.video_loop_var = tk.BooleanVar(value=self.config.get("video_loop", False))
        loop_check = tk.Checkbutton(
            self.dynamic_frame,
            text="Зациклить видео",
            variable=self.video_loop_var,
            font=('Arial', 10),
            fg='white',
            bg='#2b2b2b',
            selectcolor='#2b2b2b'
        )
        loop_check.grid(row=1, column=0, columnspan=3, sticky='w', pady=10, padx=20)
    
    def _create_image_params(self):
        """Параметры для изображения"""
        # Путь к файлу
        tk.Label(
            self.dynamic_frame,
            text="Путь к изображению:",
            font=('Arial', 10),
            fg='white',
            bg='#2b2b2b'
        ).grid(row=0, column=0, sticky='w', pady=5)
        
        self.image_path_var = tk.StringVar(value=self.config.get("image_path", "test_image.jpg"))
        
        path_entry = tk.Entry(
            self.dynamic_frame,
            textvariable=self.image_path_var,
            width=40,
            font=('Arial', 10)
        )
        path_entry.grid(row=0, column=1, sticky='w', pady=5, padx=10)
        
        browse_button = tk.Button(
            self.dynamic_frame,
            text="Обзор...",
            command=self.browse_image,
            font=('Arial', 9),
            bg='#555555',
            fg='white'
        )
        browse_button.grid(row=0, column=2, sticky='w', pady=5, padx=5)
        
        # Информация о тестовом изображении
        if not os.path.exists(self.config.get("image_path", "test_image.jpg")):
            tk.Label(
                self.dynamic_frame,
                text="⚠️ Файл test_image.jpg не найден. Будет создан тестовый черный фон.",
                font=('Arial', 9),
                fg='orange',
                bg='#2b2b2b'
            ).grid(row=1, column=0, columnspan=3, sticky='w', pady=10, padx=20)
    
    def browse_video(self):
        """Выбор видеофайла"""
        filename = filedialog.askopenfilename(
            title="Выберите видеофайл",
            filetypes=[
                ("Видео файлы", "*.mp4 *.avi *.mov *.mkv *.flv"),
                ("Все файлы", "*.*")
            ]
        )
        if filename:
            self.video_path_var.set(filename)
    
    def browse_image(self):
        """Выбор изображения"""
        filename = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[
                ("Изображения", "*.jpg *.jpeg *.png *.bmp *.tiff"),
                ("Все файлы", "*.*")
            ]
        )
        if filename:
            self.image_path_var.set(filename)
    
    def on_ok(self):
        """Обработка нажатия OK"""
        source = self.source_var.get()
        
        # Проверяем корректность выбора
        if source == "video":
            video_path = self.video_path_var.get().strip()
            if not video_path:
                messagebox.showerror("Ошибка", "Выберите видеофайл!")
                return
            if not os.path.exists(video_path):
                messagebox.showerror("Ошибка", f"Файл не найден: {video_path}")
                return
        
        if source == "image":
            image_path = self.image_path_var.get().strip()
            if not image_path:
                messagebox.showerror("Ошибка", "Выберите изображение!")
                return
        
        # Сохраняем конфигурацию
        self.config["last_selected_option"] = source
        self.config["enable_voice"] = self.voice_var.get()
        
        if source == "screen":
            self.config["monitor_number"] = self.monitor_var.get()
        elif source == "webcam":
            self.config["camera_id"] = self.camera_id_var.get()
            self.config["webcam_width"] = self.webcam_width_var.get()
            self.config["webcam_height"] = self.webcam_height_var.get()
        elif source == "video":
            self.config["video_path"] = self.video_path_var.get()
            self.config["video_loop"] = self.video_loop_var.get()
        elif source == "image":
            self.config["image_path"] = self.image_path_var.get()
        
        self.save_config()
        
        # Создаем конфигурацию для приложения
        self.result = self._build_source_config()
        self.root.quit()
        self.root.destroy()
    
    def _build_source_config(self):
        """Создание конфигурации для источника видео"""
        source = self.config["last_selected_option"]
        
        if source == "screen":
            return {
                'type': 'screen',
                'params': {
                    'monitor_number': self.config["monitor_number"],
                    'monitor_mode': 'monitor'
                }
            }
        elif source == "webcam":
            return {
                'type': 'webcam',
                'params': {
                    'camera_id': self.config["camera_id"],
                    'width': self.config["webcam_width"],
                    'height': self.config["webcam_height"]
                }
            }
        elif source == "video":
            return {
                'type': 'video',
                'params': {
                    'file_path': self.config["video_path"],
                    'loop': self.config["video_loop"]
                }
            }
        elif source == "image":
            # Проверяем существование изображения
            image_path = self.config["image_path"]
            if not os.path.exists(image_path):
                # Создаем тестовое изображение
                import cv2
                import numpy as np
                test_image = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(test_image, "Test Image", (200, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.imwrite(image_path, test_image)
                print(f"✓ Создано тестовое изображение: {image_path}")
            
            return {
                'type': 'image',
                'params': {
                    'image_path': image_path
                }
            }
        
        return {'type': 'screen', 'params': {}}
    
    def on_cancel(self):
        """Обработка отмены"""
        self.result = None
        self.root.quit()
        self.root.destroy()


def create_test_image():
    """Создание тестового изображения если его нет"""
    if not os.path.exists("test_image.jpg"):
        import cv2
        import numpy as np
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(test_image, "Test Image", (200, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imwrite("test_image.jpg", test_image)
        print("✓ Создано тестовое изображение: test_image.jpg")

        
def _add_fps_control(self, parent, default_fps=10):
    """Добавление контроля FPS"""
    tk.Label(
        parent,
        text="Макс. FPS:",
        font=('Arial', 10),
        fg='white',
        bg='#2b2b2b'
    ).grid(row=100, column=0, sticky='w', pady=5)
    
    self.fps_var = tk.IntVar(value=default_fps)
    fps_spin = tk.Spinbox(
        parent,
        from_=1,
        to=30,
        textvariable=self.fps_var,
        width=10,
        font=('Arial', 10)
    )
    fps_spin.grid(row=100, column=1, sticky='w', pady=5, padx=10)
    
    tk.Label(
        parent,
        text="(меньше FPS = меньше нагрузка на CPU)",
        font=('Arial', 9),
        fg='gray',
        bg='#2b2b2b'
    ).grid(row=100, column=2, sticky='w', pady=5, padx=10)
    
    return self.fps_var

# И обновите методы создания параметров, добавив вызов _add_fps_control:

def _create_screen_params(self):
    """Параметры для захвата экрана"""
    # ... существующий код ...
    
    # Добавляем контроль FPS
    self._add_fps_control(self.dynamic_frame, default_fps=10)

def _create_webcam_params(self):
    """Параметры для веб-камеры"""
    # ... существующий код ...
    
    # Добавляем контроль FPS
    self._add_fps_control(self.dynamic_frame, default_fps=15)

def _create_video_params(self):
    """Параметры для видеофайла"""
    # ... существующий код ...
    
    # Добавляем контроль FPS
    self._add_fps_control(self.dynamic_frame, default_fps=15)

def _create_image_params(self):
    """Параметры для изображения"""
    # ... существующий код ...
    
    # Добавляем контроль FPS
    self._add_fps_control(self.dynamic_frame, default_fps=5)
