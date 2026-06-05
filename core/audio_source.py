import pyaudio
import wave
import threading
import queue
import numpy as np
import time

class AudioSource:
    """Класс для захвата аудио с микрофона"""
    
    def __init__(self, sample_rate=16000, chunk_size=1024, channels=1):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.format = pyaudio.paInt16
        self.audio = None
        self.stream = None
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.thread = None
        
    def start(self):
        """Запуск захвата аудио"""
        self.audio = pyaudio.PyAudio()
        
        # Проверяем доступные устройства
        self._list_devices()
        
        # Открываем поток
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._audio_callback
        )
        
        self.is_recording = True
        self.stream.start_stream()
        
        # Запускаем поток для обработки аудио
        self.thread = threading.Thread(target=self._process_audio, daemon=True)
        self.thread.start()
        
        print(f"✓ Микрофон активирован (частота: {self.sample_rate} Гц)")
    
    def _list_devices(self):
        """Вывод списка аудиоустройств"""
        if self.audio:
            print("Доступные аудиоустройства:")
            for i in range(self.audio.get_device_count()):
                device_info = self.audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    print(f"  {i}: {device_info['name']}")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback для получения аудиоданных"""
        if self.is_recording:
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            self.audio_queue.put(audio_data)
        return (in_data, pyaudio.paContinue)
    
    def _process_audio(self):
        """Обработка аудио в отдельном потоке"""
        audio_buffer = []
        buffer_duration = 2  # Секунд для накопления
        samples_per_buffer = int(self.sample_rate * buffer_duration)
        
        while self.is_recording:
            try:
                # Собираем аудио в буфер
                audio_data = self.audio_queue.get(timeout=0.1)
                audio_buffer.extend(audio_data)
                
                # Если накопили достаточно данных
                if len(audio_buffer) >= samples_per_buffer:
                    # Берем последние samples_per_buffer сэмплов
                    if len(audio_buffer) > samples_per_buffer:
                        audio_buffer = audio_buffer[-samples_per_buffer:]
                    
                    # Конвертируем в numpy array
                    audio_array = np.array(audio_buffer, dtype=np.int16)
                    
                    # Нормализуем
                    audio_array = audio_array / 32768.0
                    
                    # Отправляем для распознавания
                    yield audio_array
                    
                    # Очищаем буфер (оставляем 0.5 секунды для плавности)
                    overlap = int(self.sample_rate * 0.5)
                    audio_buffer = audio_buffer[-overlap:] if len(audio_buffer) > overlap else []
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Ошибка обработки аудио: {e}")
    
    def get_audio_chunk(self, duration=2):
        """Получение чанка аудио заданной длительности"""
        samples_needed = int(self.sample_rate * duration)
        audio_buffer = []
        
        start_time = time.time()
        while len(audio_buffer) < samples_needed and time.time() - start_time < duration + 0.5:
            try:
                audio_data = self.audio_queue.get(timeout=0.1)
                audio_buffer.extend(audio_data)
            except queue.Empty:
                continue
        
        if audio_buffer:
            # Берем последние samples_needed сэмплов
            if len(audio_buffer) > samples_needed:
                audio_buffer = audio_buffer[-samples_needed:]
            
            audio_array = np.array(audio_buffer, dtype=np.int16)
            audio_array = audio_array / 32768.0
            return audio_array
        
        return None
    
    def stop(self):
        """Остановка захвата аудио"""
        self.is_recording = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        if self.audio:
            self.audio.terminate()
        
        print("✓ Микрофон деактивирован")
    
    def is_active(self):
        """Проверка активности"""
        return self.is_recording and self.stream and self.stream.is_active()