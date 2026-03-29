from customtkinter import *
from socket import *
import threading
import base64
import io
from PIL import Image, ImageTk
from tkinter.filedialog import askopenfilename
import data as d


class LogiTalk(CTk):
    def __init__(self):
        super().__init__()

        self.title("LogiTalk")
        self.geometry("400x300")
        self.minsize(400, 300)

        self.username = "Клієнт"

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Ліва панель
        self.frame = CTkFrame(self, width=200)
        self.frame.grid(row=0, column=0, rowspan=2, sticky="ns")
        self.frame.grid_propagate(False)

        self.label = CTkLabel(self.frame, text=f"Привіт, {self.username}")
        self.label.pack(pady=30)

        self.entry = CTkEntry(self.frame)
        self.entry.pack()

        CTkButton(self.frame, text="Прийняти", command=self.set_username).pack(pady=30)
        CTkOptionMenu(self.frame, values=["Світла", "Темна"], command=self.change_theme).pack(side="bottom", pady=20)

        # Чат
        self.chat_text = CTkScrollableFrame(self)
        self.chat_text.grid(row=0, column=1, sticky="nsew")

        # Нижня панель
        bottom = CTkFrame(self)
        bottom.grid(row=1, column=1, sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)

        self.message_input = CTkEntry(bottom, placeholder_text="Ваше повідомлення")
        self.message_input.grid(row=0, column=0, sticky="ew", padx=(5, 0), pady=5)
        self.message_input.bind("", lambda e: self.send_message())

        self.send_button = CTkButton(bottom, text="▶️", width=40, command=self.send_message)
        self.send_button.grid(row=0, column=1, padx=5, pady=5)

        self.open_image_button = CTkButton(bottom, text="📂", width=40, command=self.open_image)
        self.open_image_button.grid(row=0, column=2, padx=(0, 5), pady=5)

        # Підключення до сервера
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect((d.HOST, d.PORT))
            hello = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднується до чату!\n"
            self.sock.send(hello.encode())
            threading.Thread(target=self.recv_message, daemon=True).start()
        except Exception as e:
            self.add_message(f"Не вдалось підключитись: {e}")

    def set_username(self):
        self.username = self.entry.get()
        self.label.configure(text=f"Привіт, {self.username}")
        self.entry.delete(0, END)

    def add_message(self, message, img=None, own_message=False):
        bg = "#4a4a4a" if own_message else "#2d2d2d"
        f = CTkFrame(self.chat_text, fg_color=bg)
        f.pack(anchor="e" if own_message else "w", pady=5, padx=5)

        CTkLabel(f, text=message, wraplength=260, justify="left").pack(padx=10, pady=5)

        if img:
            image = Image.open(io.BytesIO(img))
            image.thumbnail((200, 200))
            photo = ImageTk.PhotoImage(image)

            lbl = CTkLabel(f, image=photo, text="")
            lbl.image = photo
            lbl.pack(padx=5, pady=5)

        # автоскрол вниз
        self.chat_text._parent_canvas.yview_moveto(1.0)

    def send_message(self):
        msg = self.message_input.get()
        if not msg:
            return

        self.add_message(f"{self.username}: {msg}", own_message=True)

        try:
            self.sock.sendall(f"TEXT@{self.username}@{msg}\n".encode())
        except:
            pass

        self.message_input.delete(0, END)

    def recv_message(self):
        buf = ""
        while True:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break

                buf += data.decode(errors="ignore")

                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    self.handle_line(line)
            except:
                break

    def handle_line(self, line):
        parts = line.split("@", 2)

        if parts[0] == "TEXT" and len(parts) == 3:
            self.add_message(f"{parts[1]}: {parts[2]}")

        elif parts[0] == "IMG" and len(parts) == 3:
            try:
                img_data = base64.b64decode(parts[2])
                self.add_message(f"{parts[1]} надіслав фото", img=img_data)
            except:
                pass

    def open_image(self):
        file_path = askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if not file_path:
            return

        with open(file_path, "rb") as f:
            img_data = f.read()

        encoded = base64.b64encode(img_data).decode()

        try:
            self.sock.sendall(f"IMG@{self.username}@{encoded}\n".encode())
        except:
            pass

        self.add_message(f"{self.username} надіслав фото", img=img_data, own_message=True)

    def change_theme(self, value):
        set_appearance_mode("dark" if value == "Темна" else "light")


LogiTalk().mainloop()