import yt_dlp
import os

class Downloader:
    def __init__(self, output_path="downloads"):
        self.output_path = output_path
        if not os.path.exists(output_path):
            os.makedirs(output_path)

    def download_video(self, url):
        """Download video (mp4)"""
        ydl_opts = {
            'outtmpl': f'{self.output_path}/%(title)s.%(ext)s',
            'format': 'bestvideo+bestaudio/best'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    def download_audio(self, url):
        """Download audio (mp3)"""
        ydl_opts = {
            'outtmpl': f'{self.output_path}/%(title)s.%(ext)s',
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
