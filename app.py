from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import tempfile
import shutil

app = Flask(__name__)

def download_video(url):
    downloads_dir = os.path.join(os.path.dirname(__file__), 'downloads')
    os.makedirs(downloads_dir, exist_ok=True)
    
    try:
        def progress_hook(d):
            if d['status'] == 'downloading':
                progress = {
                    'downloaded': d.get('downloaded_bytes', 0),
                    'total': d.get('total_bytes', 0),
                    'speed': d.get('speed', 0),
                    'eta': d.get('eta', 0)
                }
                print(progress)

        quality = request.form.get('quality', 'best')
        format_spec = {
            'highest': 'best',
            '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
            '360p': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
            'audio': 'bestaudio/best'
        }

        ydl_opts = {
            'format': format_spec.get(quality, 'best'),
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [progress_hook],
            'outtmpl': os.path.join(downloads_dir, '%(title)s.%(ext)s')
        }

        if quality == 'audio':
            ydl_opts.update({
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(downloads_dir, '%(title)s.%(ext)s')
            })
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if quality == 'audio':
                file_path = os.path.splitext(file_path)[0] + '.mp3'
            return {'success': True, 'title': info['title'], 'file_path': file_path}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if request.is_json:
            # Handle JSON request (for progress updates)
            data = request.get_json()
            video_url = data.get('url')
            quality = data.get('quality')
            if video_url:
                result = download_video(video_url)
                if result['success']:
                    try:
                        filename = os.path.basename(result['file_path'])
                        return send_file(
                            result['file_path'],
                            as_attachment=True,
                            download_name=filename,
                            mimetype='application/octet-stream'
                        )
                    finally:
                        try:
                            shutil.rmtree(os.path.dirname(result['file_path']))
                        except:
                            pass
                return jsonify({'error': result.get('error', 'Download failed')})
        else:
            # Handle form submission
            video_url = request.form.get('url')
            if video_url:
                result = download_video(video_url)
                if result['success']:
                    try:
                        filename = os.path.basename(result['file_path'])
                        return send_file(
                            result['file_path'],
                            as_attachment=True,
                            download_name=filename,
                            mimetype='application/octet-stream'
                        )
                    finally:
                        try:
                            shutil.rmtree(os.path.dirname(result['file_path']))
                        except:
                            pass
    
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)