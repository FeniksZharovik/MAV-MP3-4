import os
import re
import shutil
import unicodedata
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import yt_dlp

app = Flask(__name__)
app.secret_key = "supersecret"

# Folder download
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# favicon route
@app.route('/favicon.ico')
def favicon():
    return send_file(
        os.path.join(app.root_path, 'static', 'favicon.ico'),
        mimetype='image/vnd.microsoft.icon'
    )

# cek ffmpeg
FFMPEG_PATH = shutil.which("ffmpeg")
if not FFMPEG_PATH:
    FFMPEG_PATH = r"C:\ffmpeg\ffmpeg-8.0-full_build\bin\ffmpeg.exe"

def sanitize_filename(name, ext):
    """Buat nama file aman untuk Windows, transliterasi non-ASCII"""
    # hapus karakter ilegal Windows
    name = re.sub(r'[<>:"/\\|?*]', '', name)

    # normalisasi Unicode -> ASCII (transliterate)
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", errors="ignore").decode("ascii")

    # hapus newline dan spasi berlebih
    name = name.replace("\n", "").replace("\r", "").strip()

    if not name:
        name = "download"

    # batasi panjang nama (biar aman di Windows)
    name = name[:80]

    return f"{name}{ext}"

def download_media(url, download_type):
    ydl_opts = {
        "ffmpeg_location": FFMPEG_PATH,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),  # pakai ID unik
        "prefer_ffmpeg": True,
        "restrictfilenames": True,
        "allow_unplayable_formats": False,
        "progress_hooks": [progress_hook],  # progress callback
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

        ext = ".mp3" if download_type == "mp3" else ".mp4"
        title = info.get("title", "unknown")

        # buat nama file aman
        safe_name = sanitize_filename(title, ext)
        safe_path = os.path.join(DOWNLOAD_FOLDER, safe_name)

        # rename hasil download agar pakai judul
        base, _ = os.path.splitext(filename)
        candidate = base + ext
        if os.path.exists(candidate):
            os.rename(candidate, safe_path)
        elif os.path.exists(filename):
            os.rename(filename, safe_path)

        print(f"[DEBUG] File disimpan: {safe_path}")
        return safe_path, safe_name, title

# simpan progress download di sini (global sementara)
progress_data = {"status": "", "percent": 0}

def progress_hook(d):
    """Hook progress yt_dlp -> update ke variabel global"""
    if d['status'] == 'downloading':
        percent = d.get("_percent_str", "0.0%").strip()
        try:
            percent_value = float(percent.replace("%", ""))
        except:
            percent_value = 0
        progress_data["status"] = "downloading"
        progress_data["percent"] = percent_value
    elif d['status'] == 'finished':
        progress_data["status"] = "finished"
        progress_data["percent"] = 100

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
            file_path, file_name, title = download_media(url, download_type)
            # setelah selesai -> arahkan ke halaman result
            return render_template("result.html", file=file_name)
        except Exception as e:
            flash(f"Gagal: {str(e)}")
            return redirect(url_for("index"))

    return render_template("index.html")

@app.route("/progress")
def progress():
    """Endpoint untuk progress bar (dipanggil AJAX)"""
    return {
        "status": progress_data["status"],
        "percent": progress_data["percent"]
    }

@app.route("/download/<path:filename>")
def download_file(filename):
    """Endpoint untuk download file yang sudah selesai"""
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash("File tidak ditemukan!")
        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
