from flask import Flask, render_template, request, send_file, jsonify
from markupsafe import Markup
from flask_recaptcha import ReCaptcha
from dotenv import load_dotenv
import yt_dlp
import os
import tempfile
import shutil

load_dotenv()

app = Flask(__name__)

# Configure ReCaptcha using environment variables
app.config['RECAPTCHA_SITE_KEY'] = os.getenv('RECAPTCHA_SITE_KEY')
app.config['RECAPTCHA_SECRET_KEY'] = os.getenv('RECAPTCHA_SECRET_KEY')
app.config['RECAPTCHA_ENABLED'] = True
recaptcha = ReCaptcha(app)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if recaptcha.verify():
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
        else:
            return jsonify({'error': 'Please complete the CAPTCHA verification'}), 400
    
    return render_template('index.html', recaptcha=recaptcha)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
