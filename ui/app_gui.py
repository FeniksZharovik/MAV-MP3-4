import tkinter as tk
from tkinter import messagebox
from downloader.video_downloader import Downloader
import threading

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube & FB Downloader")
        self.root.geometry("500x300")
        self.root.config(bg="#1e1e2e")

        self.downloader = Downloader()

        # Judul
        title = tk.Label(root, text="Media Downloader", font=("Arial", 18, "bold"), fg="white", bg="#1e1e2e")
        title.pack(pady=10)

        # Input URL
        self.url_entry = tk.Entry(root, width=50, font=("Arial", 12))
        self.url_entry.pack(pady=10)

        # Tombol
        frame = tk.Frame(root, bg="#1e1e2e")
        frame.pack(pady=10)

        btn_video = tk.Button(frame, text="Download Video (MP4)", font=("Arial", 12), bg="#4caf50", fg="white",
                              command=self.download_video)
        btn_video.grid(row=0, column=0, padx=5)

        btn_audio = tk.Button(frame, text="Download Audio (MP3)", font=("Arial", 12), bg="#2196f3", fg="white",
                              command=self.download_audio)
        btn_audio.grid(row=0, column=1, padx=5)

        # Status
        self.status_label = tk.Label(root, text="", font=("Arial", 10), fg="white", bg="#1e1e2e")
        self.status_label.pack(pady=10)

    def run_in_thread(self, func):
        thread = threading.Thread(target=func)
        thread.start()

    def download_video(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Error", "Masukkan URL terlebih dahulu!")
            return
        self.status_label.config(text="Mengunduh video...")
        self.run_in_thread(lambda: self._download("video", url))

    def download_audio(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Error", "Masukkan URL terlebih dahulu!")
            return
        self.status_label.config(text="Mengunduh audio...")
        self.run_in_thread(lambda: self._download("audio", url))

    def _download(self, mode, url):
        try:
            if mode == "video":
                self.downloader.download_video(url)
                messagebox.showinfo("Sukses", "Video berhasil diunduh!")
            else:
                self.downloader.download_audio(url)
                messagebox.showinfo("Sukses", "Audio berhasil diunduh!")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal mengunduh: {str(e)}")
        finally:
            self.status_label.config(text="Selesai")
