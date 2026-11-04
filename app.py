import os
import tempfile
from flask import Flask, request, send_file, render_template_string
import yt_dlp

app = Flask(__name__)

HTML_TEMPLATE = '''
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Private YouTube Downloader</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 550px; margin: 80px auto; padding: 30px; background: #f9f9fb; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        h2 { color: #1a1a1a; margin-top: 0; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #444; }
        input[type="text"] { width: 100%; padding: 12px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 6px; font-size: 15px; }
        .button-container { display: flex; gap: 12px; }
        button { flex: 1; padding: 12px 20px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: 600; color: white; transition: background 0.2s; }
        .btn-mp4 { background: #1a73e8; }
        .btn-mp4:hover { background: #1557b0; }
        .btn-mp3 { background: #34a853; }
        .btn-mp3:hover { background: #2b8c44; }
    </style>
</head>
<body>
    <h2>YouTube Downloader</h2>
    <form method="POST" action="/download">
        <div class="form-group">
            <label for="url">Paste YouTube URL:</label>
            <input type="text" id="url" name="url" required placeholder="https://www.youtube.com/watch?v=...">
        </div>
        <div class="button-container">
            <button type="submit" name="format" value="mp4" class="btn-mp4">Download MP4 (H.264)</button>
            <button type="submit" name="format" value="mp3" class="btn-mp3">Download MP3</button>
        </div>
    </form>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download_file():
    url = request.form.get('url')
    format_type = request.form.get('format', 'mp4')

    if not url:
        return "Error: No URL provided", 400

    # Secure temporary directory for processing
    tmp_dir = tempfile.mkdtemp()
    
    ydl_opts = {
        'outtmpl': os.path.join(tmp_dir, '%(title)s.%(ext)s'),
        'noplaylist': True,
        # Bypass bot detection by forcing alternative client players
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        }
    }

    if format_type == 'mp3':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:  # H.264 MP4 preference for local MacBook playback
        ydl_opts.update({
            'format': 'bestvideo[vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if format_type == 'mp3':
                filename = os.path.splitext(filename)[0] + '.mp3'
            elif not filename.endswith('.mp4'):
                filename = os.path.splitext(filename)[0] + '.mp4'

        return send_file(filename, as_attachment=True)
    except Exception as e:
        return f"An error occurred during download: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)