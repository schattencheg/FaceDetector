import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk

class FaceManagerWindow:
    """Окно управления базой лиц"""
    
    def __init__(self, face_manager):
        self.face_manager = face_manager
        self.root = None
        self.result = None
    
    def show(self):
        """Отображение окна управления"""
        self.root = tk.Tk()
        self.root.title("Управление базой лиц")
        self.root.geometry("600x500")
        self.root.configure(bg='#2b2b2b')
        
        # Центрируем окно
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.root.winfo_screenheight() // 2) - (500 // 2)
        self.root.geometry(f"600x500+{x}+{y}")
        
        self.root.attributes('-topmost', True)
        
        # Заголовок
        title_label = tk.Label(
            self.root,
            text="Управление базой известных лиц",
            font=('Arial', 14, 'bold'),
            fg='white',
            bg='#2b2b2b'
        )
        title_label.pack(pady=10)
        
        # Список лиц
        list_frame = tk.LabelFrame(
            self.root,
            text="Список лиц",
            font=('Arial', 12),
            fg='white',
            bg='#2b2b2b',
            bd=2,
            relief='groove'
        )
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Создаем список с прокруткой
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.listbox = tk.Listbox(
            list_frame,
            font=('Arial', 11),
            bg='#3c3c3c',
            fg='white',
            selectbackground='#4CAF50',
            yscrollcommand=scrollbar.set
        )
        self.listbox.pack(fill='both', expand=True, padx=10, pady=10)
        scrollbar.config(command=self.listbox.yview)
        
        # Заполняем список
        self.refresh_list()
        
        # Кнопки управления
        button_frame = tk.Frame(self.root, bg='#2b2b2b')
        button_frame.pack(fill='x', padx=20, pady=10)
        
        rename_btn = tk.Button(
            button_frame,
            text="Переименовать",
            command=self.rename_face,
            font=('Arial', 11),
            bg='#2196F3',
            fg='white',
            padx=20,
            pady=5
        )
        rename_btn.pack(side='left', padx=5)
        
        delete_btn = tk.Button(
            button_frame,
            text="Удалить",
            command=self.delete_face,
            font=('Arial', 11),
            bg='#f44336',
            fg='white',
            padx=20,
            pady=5
        )
        delete_btn.pack(side='left', padx=5)
        
        view_btn = tk.Button(
            button_frame,
            text="Просмотреть",
            command=self.view_face,
            font=('Arial', 11),
            bg='#FF9800',
            fg='white',
            padx=20,
            pady=5
        )
        view_btn.pack(side='left', padx=5)
        
        refresh_btn = tk.Button(
            button_frame,
            text="Обновить",
            command=self.refresh_list,
            font=('Arial', 11),
            bg='#9C27B0',
            fg='white',
            padx=20,
            pady=5
        )
        refresh_btn.pack(side='left', padx=5)
        
        close_btn = tk.Button(
            button_frame,
            text="Закрыть",
            command=self.root.destroy,
            font=('Arial', 11),
            bg='#555555',
            fg='white',
            padx=20,
            pady=5
        )
        close_btn.pack(side='right', padx=5)
        
        # Информация
        info_label = tk.Label(
            self.root,
            text="Совет: Нажмите 'm' в главном окне для открытия этого меню",
            font=('Arial', 9),
            fg='gray',
            bg='#2b2b2b'
        )
        info_label.pack(pady=5)
        
        self.root.mainloop()
    
    def refresh_list(self):
        """Обновление списка лиц"""
        self.listbox.delete(0, tk.END)
        self.face_manager.face_storage.load_faces()  # Перезагружаем базу
        
        for name in self.face_manager.face_storage.known_names:
            self.listbox.insert(tk.END, name)
        
        count = self.listbox.size()
        if count == 0:
            self.listbox.insert(tk.END, "(пусто)")
    
    def rename_face(self):
        """Переименование выбранного лица"""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите лицо для переименования")
            return
        
        old_name = self.listbox.get(selection[0])
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Переименование")
        dialog.geometry("400x150")
        dialog.configure(bg='#2b2b2b')
        dialog.attributes('-topmost', True)
        
        tk.Label(
            dialog,
            text=f"Введите новое имя для '{old_name}':",
            font=('Arial', 11),
            fg='white',
            bg='#2b2b2b'
        ).pack(pady=20)
        
        entry = tk.Entry(dialog, font=('Arial', 11), width=30)
        entry.pack(pady=10)
        entry.focus()
        
        def on_ok():
            new_name = entry.get().strip()
            if new_name:
                success, message = self.face_manager.rename_face(old_name, new_name)
                if success:
                    messagebox.showinfo("Успех", message)
                    self.refresh_list()
                    dialog.destroy()
                else:
                    messagebox.showerror("Ошибка", message)
            else:
                messagebox.showwarning("Внимание", "Имя не может быть пустым")
        
        def on_cancel():
            dialog.destroy()
        
        button_frame = tk.Frame(dialog, bg='#2b2b2b')
        button_frame.pack(pady=10)
        
        tk.Button(
            button_frame,
            text="OK",
            command=on_ok,
            bg='#4CAF50',
            fg='white',
            padx=20,
            pady=5
        ).pack(side='left', padx=10)
        
        tk.Button(
            button_frame,
            text="Отмена",
            command=on_cancel,
            bg='#f44336',
            fg='white',
            padx=20,
            pady=5
        ).pack(side='left', padx=10)
        
        entry.bind('<Return>', lambda event: on_ok())
    
    def delete_face(self):
        """Удаление выбранного лица"""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите лицо для удаления")
            return
        
        name = self.listbox.get(selection[0])
        
        result = messagebox.askyesno(
            "Подтверждение",
            f"Вы уверены, что хотите удалить лицо '{name}'?\n\nЭто действие нельзя отменить.",
            icon='warning'
        )
        
        if result:
            success, message = self.face_manager.delete_face(name)
            if success:
                messagebox.showinfo("Успех", message)
                self.refresh_list()
            else:
                messagebox.showerror("Ошибка", message)
    
    def view_face(self):
        """Просмотр выбранного лица"""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите лицо для просмотра")
            return
        
        name = self.listbox.get(selection[0])
        image = self.face_manager.get_face_image(name)
        
        if image is not None:
            view_window = tk.Toplevel(self.root)
            view_window.title(f"Лицо: {name}")
            view_window.geometry("400x450")
            view_window.configure(bg='#2b2b2b')
            view_window.attributes('-topmost', True)
            
            # Изменяем размер для отображения
            display_image = cv2.resize(image, (300, 300))
            display_image = cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB)
            
            from PIL import Image, ImageTk
            image_pil = Image.fromarray(display_image)
            photo = ImageTk.PhotoImage(image_pil)
            
            image_label = tk.Label(view_window, image=photo, bg='#2b2b2b')
            image_label.image = photo
            image_label.pack(pady=20)
            
            name_label = tk.Label(
                view_window,
                text=f"Имя: {name}",
                font=('Arial', 14, 'bold'),
                fg='white',
                bg='#2b2b2b'
            )
            name_label.pack(pady=10)
            
            close_btn = tk.Button(
                view_window,
                text="Закрыть",
                command=view_window.destroy,
                bg='#4CAF50',
                fg='white',
                padx=20,
                pady=5
            )
            close_btn.pack(pady=10)
        else:
            messagebox.showerror("Ошибка", "Не удалось загрузить изображение")