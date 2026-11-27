"""Regras de download, separadas da interface."""
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
import re
import shutil
import importlib.util

VIDEO_QUALITIES = ("Melhor disponível", "2160p (4K)", "1440p", "1080p", "720p", "480p", "360p")
AUDIO_QUALITIES = ("320 kbps", "192 kbps", "128 kbps")
FPS_OPTIONS = ("Automático", "30 FPS", "60 FPS")
VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}")


def youtube_url(text):
    """Aceita vídeos individuais e remove parâmetros de playlists e rastreamento."""
    text = text.strip()
    if not text:
        raise ValueError("Cole o link de um vídeo do YouTube.")
    if '://' not in text:
        text = 'https://' + text
    try:
        u = urlsplit(text)
        host = u.hostname
    except ValueError:
        raise ValueError("Link inválido.") from None
    if u.scheme not in ('http', 'https') or u.username or u.password:
        raise ValueError("Use um link válido do YouTube.")
    parts = u.path.strip('/').split('/')
    video_id = None
    if host == 'youtu.be':
        video_id = parts[0] if len(parts) == 1 else None
    elif host in ('youtube.com', 'www.youtube.com', 'm.youtube.com', 'music.youtube.com'):
        if u.path == '/watch':
            video_id = parse_qs(u.query).get('v', [''])[0]
        elif len(parts) == 2 and parts[0] in ('shorts', 'live', 'embed'):
            video_id = parts[1]
    if not video_id or not VIDEO_ID.fullmatch(video_id):
        raise ValueError("Use o link de um vídeo individual do YouTube, Shorts ou youtu.be.")
    return 'https://www.youtube.com/watch?v=' + video_id


def missing_dependencies():
    missing = []
    if importlib.util.find_spec('yt_dlp') is None:
        missing.append('yt-dlp: python -m pip install -r requirements.txt')
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        missing.append('FFmpeg e ffprobe (instale e adicione ao PATH).')
    if not shutil.which('deno'):
        missing.append('Deno (instale e adicione ao PATH).')
    return missing


def make_options(folder, mode, quality, progress_hook, post_hook, fps="Automático"):
    """Escolhe o formato e limita a resolução sem aumentar a qualidade original."""
    folder = Path(folder).expanduser().resolve()
    if not folder.is_dir():
        raise ValueError('Escolha uma pasta de destino existente.')
    opts = {
        'paths': {'home': str(folder)},
        'outtmpl': {'default': '%(title).150B [%(id)s].%(ext)s'},
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'windowsfilenames': True,
        'overwrites': False,
        'socket_timeout': 25,
        'retries': 3,
        'fragment_retries': 5,
        'nocolor': True,
        'progress_hooks': [progress_hook],
        'postprocessor_hooks': [post_hook],
    }
    if mode == 'MP3':
        if quality not in AUDIO_QUALITIES:
            raise ValueError('Qualidade de áudio inválida.')
        opts.update(format='bestaudio/best', postprocessors=[{
            'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3',
            'preferredquality': quality.split()[0],
        }])
    elif mode == 'MP4':
        if quality not in VIDEO_QUALITIES:
            raise ValueError('Qualidade de vídeo inválida.')
        limit = '' if quality == VIDEO_QUALITIES[0] else f'[height<={quality.split("p")[0]}]'
        if fps not in FPS_OPTIONS:
            raise ValueError('Taxa de quadros inválida.')
        # 29.97 e 59.94 também são taxas comuns de vídeo.
        fps_filter = {'Automático': '', '30 FPS': '[fps>=29][fps<=30.5]',
                      '60 FPS': '[fps>=59][fps<=60.5]'}[fps]
        limit += fps_filter
        opts.update(format=f'bv[ext=mp4]{limit}+ba[ext=m4a]/b[ext=mp4]{limit}',
                    merge_output_format='mp4')
    else:
        raise ValueError('Formato inválido.')
    return opts
