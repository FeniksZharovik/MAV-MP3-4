import os
import re
import shutil
import unicodedata
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import yt_dlp
from tqdm import tqdm
import sys
from colorama import Fore, Style, init

# init warna terminal
init(autoreset=True)

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
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", errors="ignore").decode("ascii")
    name = name.replace("\n", "").replace("\r", "").strip()
    if not name:
        name = "download"
    name = name[:80]
    return f"{name}{ext}"


def unique_filename(path):
    """Kalau file sudah ada, tambahkan (1), (2), dst."""
    base, ext = os.path.splitext(path)
    counter = 1
    new_path = path
    while os.path.exists(new_path):
        new_path = f"{base} ({counter}){ext}"
        counter += 1
    return new_path


# global progress
progress_data = {"status": "", "percent": 0}
pbar = None


def progress_hook(d):
    """Hook progress yt_dlp -> update progress CLI & web"""
    global pbar
    if d['status'] == 'downloading':
        percent = d.get("_percent_str", "0.0%").strip()
        try:
            percent_value = float(percent.replace("%", ""))
        except:
            percent_value = 0
        progress_data["status"] = "downloading"
        progress_data["percent"] = percent_value

        if pbar is None:
            pbar = tqdm(total=100, desc=Fore.CYAN + "Mengunduh" + Style.RESET_ALL,
                        ncols=80, file=sys.stdout)
        pbar.n = int(percent_value)
        pbar.refresh()

    elif d['status'] == 'finished':
        progress_data["status"] = "finished"
        progress_data["percent"] = 100
        if pbar:
            pbar.n = 100
            pbar.refresh()
            pbar.close()


def download_media(url, download_type):
    ydl_opts = {
        "ffmpeg_location": FFMPEG_PATH,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),  # ID unik
        "prefer_ffmpeg": True,
        "restrictfilenames": True,
        "allow_unplayable_formats": False,
        "progress_hooks": [progress_hook],
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
    else:
        ydl_opts.update({
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

        ext = ".mp3" if download_type == "mp3" else ".mp4"
        title = info.get("title", "unknown")

        safe_name = sanitize_filename(title, ext)
        safe_path = os.path.join(DOWNLOAD_FOLDER, safe_name)
        safe_path = unique_filename(safe_path)  # pastikan unik

        base, _ = os.path.splitext(filename)
        candidate = base + ext
        if os.path.exists(candidate):
            os.rename(candidate, safe_path)
        elif os.path.exists(filename):
            os.rename(filename, safe_path)

        print(Fore.GREEN + f"\n[INFO] File disimpan: {safe_path}" + Style.RESET_ALL)
        return safe_path, os.path.basename(safe_path), title


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
            return render_template("result.html", file=file_name, title=title)
        except Exception as e:
            flash(f"Gagal: {str(e)}")
            return redirect(url_for("index"))

    return render_template("index.html")


@app.route("/progress")
def progress():
    return {
        "status": progress_data["status"],
        "percent": progress_data["percent"]
    }


@app.route("/download/<path:filename>")
def download_file(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash("File tidak ditemukan!")
        return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
