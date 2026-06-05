from deepface import DeepFace
import time

class EmotionAnalyzer:
    """Класс для анализа эмоций"""
    
    EMOTION_TRANSLATION = {
        'angry': 'Злой',
        'disgust': 'Отвращение',
        'fear': 'Испуг',
        'happy': 'Счастлив',
        'sad': 'Грустный',
        'surprise': 'Удивлен',
        'neutral': 'Нейтрален'
    }
    
    def __init__(self, analysis_interval=1.5):
        self.analysis_interval = analysis_interval
        self.last_analysis_time = 0
        self.current_emotion = "Поиск лица..."
    
    def analyze(self, face_image):
        """Анализ эмоции на лице"""
        current_time = time.time()
        
        if current_time - self.last_analysis_time < self.analysis_interval:
            return self.current_emotion
        
        self.last_analysis_time = current_time
        
        try:
            analysis = DeepFace.analyze(
                img_path=face_image, 
                actions=['emotion'], 
                enforce_detection=False
            )
            dominant_emotion = analysis[0]['dominant_emotion']
            self.current_emotion = self.EMOTION_TRANSLATION.get(
                dominant_emotion, 
                dominant_emotion
            )
        except Exception:
            pass
        
        return self.current_emotion