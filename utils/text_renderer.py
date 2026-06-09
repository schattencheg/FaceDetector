import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os


class TextRenderer:
    def __init__(self, default_font_size=24):
        self.default_font_size = default_font_size
        self.font = self._load_font()
    
    def _load_font(self):
        """Загрузка шрифта с поддержкой кириллицы"""
        # Список путей к русским шрифтам
        font_paths = [
            # Windows
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/times.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            # Linux
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            # macOS
            "/System/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttf",
            # Стандартные
            "arial.ttf",
            "DejaVuSans.ttf"
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, self.default_font_size)
                    print(f"✓ Загружен шрифт: {font_path}")
                    return font
                except:
                    continue
        
        print("⚠️ Русский шрифт не найден, используется стандартный (кириллица может не отображаться)")
        return ImageFont.load_default()
    
    def draw_text(self, image, text, position, font_size=None, color=(255, 255, 255)):
        """Рисование текста с поддержкой кириллицы"""
        # Конвертируем BGR в RGB для PIL
        if len(image.shape) == 3 and image.shape[2] == 3:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = image
        
        pil_image = Image.fromarray(rgb_image)
        draw = ImageDraw.Draw(pil_image)
        
        # Выбираем шрифт
        if font_size and font_size != self.default_font_size:
            font = self._load_font_with_size(font_size)
        else:
            font = self.font
        
        # Рисуем текст
        draw.text(position, text, font=font, fill=color)
        
        # Конвертируем обратно в BGR
        result = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        return result
    
    def _load_font_with_size(self, size):
        """Загрузка шрифта определенного размера"""
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "arial.ttf"
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except:
                    continue
        
        return ImageFont.load_default()