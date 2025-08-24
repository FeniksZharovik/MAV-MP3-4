import os
import shutil
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import yt_dlp

app = Flask(__name__)
app.secret_key = "supersecret"
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Cek apakah ffmpeg ada
FFMPEG_PATH = shutil.which("ffmpeg")
if not FFMPEG_PATH:
    # fallback manual (misalnya di Windows)
    # ganti sesuai lokasi ffmpeg kamu
    FFMPEG_PATH = r"C:\ffmpeg\ffmpeg-8.0-full_build\bin"

def download_media(url, download_type):
    ydl_opts = {
        "ffmpeg_location": FFMPEG_PATH,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
        "prefer_ffmpeg": True,
        "allow_unplayable_formats": False,
    }

    if download_type == "mp3":
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })
    else:  # mp4
        ydl_opts.update({
            "format": "mp4/bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if download_type == "mp3":
            filename = os.path.splitext(filename)[0] + ".mp3"
        elif not os.path.exists(filename):
            filename = os.path.splitext(filename)[0] + ".mp4"
        return filename, info.get("title", "unknown")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        download_type = request.form.get("type")

        if not url:
            flash("Harap masukkan URL video!")
            return redirect(url_for("index"))

        if not shutil.which("ffmpeg") and not os.path.exists(os.path.join(FFMPEG_PATH, "ffmpeg.exe")):
            flash("❌ FFmpeg tidak ditemukan. Silakan install ffmpeg atau set lokasi di app.py!")
            return redirect(url_for("index"))

        try:
            file_path, title = download_media(url, download_type)
            return render_template("result.html", file=os.path.basename(file_path), title=title)
        except Exception as e:
            flash(f"Gagal: {str(e)}")
            return redirect(url_for("index"))

    return render_template("index.html")

@app.route("/download/<filename>")
def download_file(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
