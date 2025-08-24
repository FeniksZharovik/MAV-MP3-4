import os
import shutil
import re
from flask import Flask, render_template, request, send_file, redirect, url_for, flash, send_from_directory
import yt_dlp

app = Flask(__name__)
app.secret_key = "supersecret"

# Folder download
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# favicon route
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

# cek ffmpeg
FFMPEG_PATH = shutil.which("ffmpeg")
if not FFMPEG_PATH:
    # kalau manual Windows, arahkan langsung ke ffmpeg.exe
    FFMPEG_PATH = r"C:\ffmpeg\ffmpeg-8.0-full_build\bin\ffmpeg.exe"

# fungsi sanitasi nama file
def safe_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def download_media(url, download_type):
    # template nama file -> judul + id biar aman dan unik
    ydl_opts = {
        "ffmpeg_location": FFMPEG_PATH,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title).200B-%(id)s.%(ext)s"),
        "prefer_ffmpeg": True,
        "restrictfilenames": True,
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
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

        # sanitasi nama file hasil
        base, ext = os.path.splitext(filename)
        safe_name = safe_filename(os.path.basename(base)) + ext
        safe_path = os.path.join(DOWNLOAD_FOLDER, safe_name)

        if filename != safe_path:
            os.rename(filename, safe_path)

        return safe_path, info.get("title", "unknown")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        download_type = request.form.get("type")

        if not url:
            flash("Harap masukkan URL video!")
            return redirect(url_for("index"))

        if not os.path.exists(FFMPEG_PATH):
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

    if not os.path.exists(file_path):
        flash("❌ File tidak ditemukan!")
        return redirect(url_for("index"))

    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
