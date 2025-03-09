import yt_dlp
import os

def download_video(url):
    try:
        # Get Downloads folder path
        downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(downloads_path, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False
        }
        
        # Download the video
        print("Starting download...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            print(f"\nTitle: {info['title']}")
            print("Download completed!")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # Get video URL from user
    video_url = input("Enter the YouTube video URL: ")
    download_video(video_url)