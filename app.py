from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import tempfile
import shutil

app = Flask(__name__)

def download_video(url, quality='best'):
    downloads_dir = os.path.join(os.path.dirname(__file__), 'downloads')
    os.makedirs(downloads_dir, exist_ok=True)
    
    try:
        format_spec = {
            'highest': 'bestvideo+bestaudio/best',  # Changed to ensure best quality
            '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
            '360p': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
            'audio': 'bestaudio/best'
        }

        ydl_opts = {
            'format': format_spec.get(quality, 'bestvideo+bestaudio/best'),
            'quiet': False,
            'no_warnings': False,
            'merge_output_format': 'mp4',  # Added to ensure proper merging
            'outtmpl': os.path.join(downloads_dir, '%(title)s.%(ext)s'),
            'nocheckcertificate': True,    # Added to avoid SSL issues
            'ignoreerrors': False,         # Don't ignore errors
            'no_color': True              # Disable colors in output
        }

        if quality == 'audio':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            })
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if quality == 'audio':
                file_path = os.path.splitext(file_path)[0] + '.mp3'
            elif 'mp4' not in file_path:
                file_path = os.path.splitext(file_path)[0] + '.mp4'
            
            # Wait for file to be fully written
            if os.path.exists(file_path):
                return {'success': True, 'title': info['title'], 'file_path': file_path}
            else:
                raise Exception("File download failed")
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        video_url = request.form.get('url') or request.json.get('url')
        quality = request.form.get('quality') or request.json.get('quality', 'best')
        
        if video_url:
            result = download_video(video_url, quality)
            if result['success']:
                try:
                    filename = os.path.basename(result['file_path'])
                    response = send_file(
                        result['file_path'],
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/octet-stream'
                    )
                    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    return response
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
                finally:
                    try:
                        if os.path.exists(result['file_path']):
                            os.remove(result['file_path'])
                    except:
                        pass
            return jsonify({'error': result.get('error', 'Download failed')}), 400
    
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
