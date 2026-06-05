import cv2

class Drawer:
    """Класс для отрисовки графики на видео"""
    
    def __init__(self, text_renderer):
        self.text_renderer = text_renderer
        self.colors = {
            'unknown': (0, 0, 255),      # Красный
            'known': (0, 255, 0),        # Зеленый
            'learning': (0, 255, 255),   # Желтый
            'highlight': (0, 255, 255),  # Желтый для подсветки
            'white': (255, 255, 255),
            'gray': (128, 128, 128)
        }
    
    def draw_face(self, frame, face, name, emotion, is_learning_mode=False, is_highlight=False):
        """Отрисовка одного лица"""
        x, y, w, h = face
        
        # Определяем цвет рамки
        if name == "Чужой":
            if is_learning_mode:
                color = self.colors['learning']
                status_text = "НОВОЕ ЛИЦО"
            else:
                color = self.colors['unknown']
                status_text = "ЧУЖОЙ"
        else:
            color = self.colors['known']
            status_text = f"СВОЙ: {name}"
        
        # Рисуем рамку
        if is_highlight:
            cv2.rectangle(frame, (x, y), (x + w, y + h), self.colors['highlight'], 2)
        else:
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)
        
        # Рисуем текст
        frame = self.text_renderer.draw_text(
            frame, status_text, (x, y - 35), 24, color
        )
        frame = self.text_renderer.draw_text(
            frame, f"Эмоция: {emotion}", (x, y - 10), 24, self.colors['white']
        )
        
        return frame
    
    def draw_info_panel(self, frame, known_count, is_learning_mode, is_paused=False):
        """Отрисовка информационной панели"""
        if is_paused:
            # Затемнение экрана
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 0), -1)
            frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
            
            frame = self.text_renderer.draw_text(
                frame, "ДОБАВЛЕНИЕ НОВОГО ЛИЦА...",
                (frame.shape[1]//2 - 200, frame.shape[0]//2), 32, self.colors['white']
            )
            frame = self.text_renderer.draw_text(
                frame, "Пожалуйста, подождите",
                (frame.shape[1]//2 - 150, frame.shape[0]//2 + 50), 24, self.colors['gray']
            )
        elif is_learning_mode:
            frame = self.text_renderer.draw_text(
                frame, "РЕЖИМ ОБУЧЕНИЯ: ВКЛ (нажмите 'l' для выхода)",
                (10, 30), 24, self.colors['learning']
            )
            frame = self.text_renderer.draw_text(
                frame, "Наведитесь на лицо и нажмите ENTER для добавления",
                (10, 65), 20, self.colors['learning']
            )
        else:
            frame = self.text_renderer.draw_text(
                frame, "РЕЖИМ ОБУЧЕНИЯ: ВЫКЛ (нажмите 'l' для входа)",
                (10, 30), 24, self.colors['gray']
            )
        
        # Информация о количестве лиц
        info_text = f"Известных лиц: {known_count}"
        frame = self.text_renderer.draw_text(
            frame, info_text,
            (10, frame.shape[0] - 30), 20, self.colors['white']
        )
        
        return frame
    
    def draw_help(self, frame):
        """Отрисовка подсказок"""
        y_offset = frame.shape[0] - 80
        help_texts = [
            "q - Выход | l - Обучение | s - Скриншот | r - Перезагрузка"
        ]
        
        for i, text in enumerate(help_texts):
            frame = self.text_renderer.draw_text(
                frame, text,
                (10, y_offset + i * 25), 16, self.colors['gray']
            )
        
        return frame