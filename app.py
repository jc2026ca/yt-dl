import os
import tempfile
from flask import Flask, render_template_string, request, send_file
import yt_dlp

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Downloader</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f4f4f9; color: #333; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 100%; max-width: 450px; }
        h2 { margin-top: 0; color: #111; text-align: center; }
        label { display: block; margin-bottom: 0.5rem; font-weight: 600; }
        input[type="text"], select { width: 100%; padding: 0.75rem; margin-bottom: 1.25rem; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; }
        button { width: 100%; padding: 0.75rem; background: #ff0000; color: white; border: none; border-radius: 6px; font-size: 1rem; font-weight: bold; cursor: pointer; }
        button:hover { background: #cc0000; }
        .error { color: #d9534f; background: #f9eded; padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="card">
        <h2>YouTube Downloader</h2>
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST" action="/download">
            <label for="url">YouTube URL:</label>
            <input type="text" id="url" name="url" placeholder="https://www.youtube.com/watch?v=..." required>
            
            <label for="format">Format / Quality:</label>
            <select id="format" name="format">
                <option value="mp4">MP4 Video (MacBook Compatible)</option>
                <option value="mp3">MP3 (Audio Only)</option>
            </select>
            
            <button type="submit">Download</button>
        </form>
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    fmt = request.form.get("format")

    if not url:
        return render_template_string(HTML_TEMPLATE, error="Please provide a valid YouTube URL.")

    tmp_dir = tempfile.mkdtemp()
    
    ydl_opts = {
        'outtmpl': os.path.join(tmp_dir, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        }
    }

    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = "cookies.txt"

    if fmt == "mp3":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        # Let yt-dlp select the best available default stream without strict format constraints
        ydl_opts.update({
            'format': 'b',
            'merge_output_format': 'mp4',
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if fmt == "mp3":
                filename = os.path.splitext(filename)[0] + ".mp3"
            elif not filename.endswith(".mp4"):
                filename = os.path.splitext(filename)[0] + ".mp4"

            if not os.path.exists(filename):
                files = os.listdir(tmp_dir)
                if files:
                    filename = os.path.join(tmp_dir, files[0])
                else:
                    raise Exception("Downloaded file could not be located.")

            return send_file(filename, as_attachment=True)

    except Exception as e:
        return render_template_string(HTML_TEMPLATE, error=f"An error occurred during download: {str(e)}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)