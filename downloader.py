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
