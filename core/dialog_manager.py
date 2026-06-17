import tkinter as tk
import threading

class DialogManager:
    """Класс для управления диалоговыми окнами"""
    
    def __init__(self):
        self.is_open = False
        self.result = None
        self._done_event = threading.Event()
    
    def show_add_face_dialog(self, face_image):
        """Показать диалог добавления лица"""
        self.is_open = True
        self.result = None
        self._done_event.clear()
        
        def create_dialog():
            try:
                root = tk.Tk()
                root.title("Новое лицо")
                root.geometry("500x550")
                root.configure(bg='#2b2b2b')
                root.attributes('-topmost', True)
                root.grab_set()
                root.focus_force()
                
                # Показываем лицо
                if face_image is not None:
                    import cv2
                    from PIL import Image, ImageTk
                    
                    display_image = cv2.resize(face_image, (250, 250))
                    display_image = cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB)
                    image_pil = Image.fromarray(display_image)
                    photo = ImageTk.PhotoImage(image_pil)
                    
                    image_label = tk.Label(root, image=photo, bg='#2b2b2b')
                    image_label.image = photo
                    image_label.pack(pady=20)
                
                label = tk.Label(
                    root, 
                    text="Введите имя для этого лица:", 
                    font=('Arial', 14), 
                    fg='white', 
                    bg='#2b2b2b'
                )
                label.pack(pady=10)
                
                entry = tk.Entry(root, font=('Arial', 12), width=30)
                entry.pack(pady=10)
                entry.focus()
                
                def on_ok():
                    name = entry.get().strip()
                    if name:
                        self.result = name
                        root.destroy()
                
                def on_cancel():
                    self.result = None
                    root.destroy()
                
                button_frame = tk.Frame(root, bg='#2b2b2b')
                button_frame.pack(pady=20)
                
                ok_button = tk.Button(
                    button_frame, text="Сохранить", command=on_ok,
                    font=('Arial', 12), bg='#4CAF50', fg='white', 
                    padx=20, pady=5
                )
                ok_button.pack(side=tk.LEFT, padx=10)
                
                cancel_button = tk.Button(
                    button_frame, text="Пропустить", command=on_cancel,
                    font=('Arial', 12), bg='#f44336', fg='white', 
                    padx=20, pady=5
                )
                cancel_button.pack(side=tk.LEFT, padx=10)
                
                entry.bind('<Return>', lambda event: on_ok())
                root.protocol("WM_DELETE_WINDOW", on_cancel)
                
                root.mainloop()
            except Exception as e:
                print(f"Error in dialog: {e}")
            finally:
                self.is_open = False
                self._done_event.set()
        
        thread = threading.Thread(target=create_dialog, daemon=True)
        thread.start()
        
        self._done_event.wait()
        return self.result