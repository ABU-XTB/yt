from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import tempfile
import shutil
import cloudscraper
import random

app = Flask(__name__)

def download_video(url, quality='best'):
    downloads_dir = os.path.join(os.path.dirname(__file__), 'downloads')
    os.makedirs(downloads_dir, exist_ok=True)
    
    try:
        # Create a cloudscraper session
        scraper = cloudscraper.create_scraper()
        
        format_spec = {
            'highest': 'best',
            '1080p': 'bestvideo[height<=1080]+bestaudio/best',
            '720p': 'bestvideo[height<=720]+bestaudio/best',
            '480p': 'bestvideo[height<=480]+bestaudio/best',
            '360p': 'bestvideo[height<=360]+bestaudio/best',
            'audio': 'bestaudio/best'
        }

        # List of common user agents
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/119.0.0.0',
        ]

        ydl_opts = {
            'format': format_spec.get(quality, 'best'),
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
            'outtmpl': os.path.join(downloads_dir, '%(title)s.%(ext)s'),
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'no_color': True,
            'noprogress': True,
            'noplaylist': True,
            'extract_flat': False,
            'youtube_include_dash_manifest': True,
            'http_headers': {
                'User-Agent': random.choice(user_agents),
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Range': 'bytes=0-',
                'Referer': 'https://www.youtube.com/',
                'Origin': 'https://www.youtube.com',
                'Connection': 'keep-alive',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['web', 'android'],
                    'player_skip': ['js'],
                }
            },
            'socket_timeout': 15,
            'retries': 3,
            'source_address': '0.0.0.0',
        }

        def download_with_fallback():
            try:
                # First try: Use cloudscraper to get cookies
                cookies = scraper.get('https://www.youtube.com').cookies
                ydl_opts['cookiesfrombrowser'] = ('chrome', None, None, None)
                ydl_opts['cookiefile'] = None
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(url, download=True)
            except Exception as e:
                # Second try: Basic format with different user agent
                basic_opts = ydl_opts.copy()
                basic_opts.update({
                    'format': 'best[protocol^=http]',
                    'http_headers': {'User-Agent': random.choice(user_agents)},
                })
                with yt_dlp.YoutubeDL(basic_opts) as ydl:
                    return ydl.extract_info(url, download=True)

        if quality == 'audio':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            })

        # Try alternative format if initial download fails
        def download_with_fallback():
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    return info
            except Exception as e:
                if 'This video is not available' in str(e):
                    # Try with basic format
                    ydl_opts['format'] = 'best'
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        return ydl.extract_info(url, download=True)
                raise e

        info = download_with_fallback()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
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
