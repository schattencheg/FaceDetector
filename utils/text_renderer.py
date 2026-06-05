import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

class TextRenderer:
    """Класс для рендеринга текста с поддержкой кириллицы"""
    
    def __init__(self, default_font_size=24):
        self.default_font_size = default_font_size
        self.font = self._load_font()
    
    def _load_font(self):
        """Загрузка шрифта с поддержкой кириллицы"""
        font_paths = [
            "arial.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Arial.ttf"
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, self.default_font_size)
                except:
                    continue
        
        return ImageFont.load_default()
    
    def draw_text(self, image, text, position, font_size=None, color=(255, 255, 255)):
        """Рисование текста на изображении"""
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        draw = ImageDraw.Draw(pil_image)
        
        font = self.font
        if font_size and font_size != self.default_font_size:
            # Временно создаем шрифт другого размера
            font = self._load_font_with_size(font_size)
        
        draw.text(position, text, font=font, fill=color)
        
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    def _load_font_with_size(self, size):
        """Загрузка шрифта определенного размера"""
        font_paths = [
            "arial.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Arial.ttf"
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except:
                    continue
        
        return ImageFont.load_default()