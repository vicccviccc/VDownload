"""Regras de download, separadas da interface."""
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
import re
import os
import math
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
    if any(ord(char) < 32 or ord(char) == 127 for char in text):
        raise ValueError('O link contém caracteres inválidos.')
    if '://' not in text:
        text = 'https://' + text
    try:
        u = urlsplit(text)
        host = u.hostname
        port = u.port
    except ValueError:
        raise ValueError("Link inválido.") from None
    if u.scheme not in ('http', 'https') or u.username is not None or u.password is not None or port not in (None, 80, 443):
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
    if not os.access(folder, os.W_OK):
        raise ValueError('A pasta de destino não tem permissão de escrita.')
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


def valid_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) and number >= 0 else None


def human_size(value):
    n = valid_number(value)
    if n is None:
        return '—'
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024 or unit == 'GB':
            return f'{n:.1f} {unit}'
        n /= 1024


def progress_data(data):
    total = valid_number(data.get('total_bytes')) or valid_number(data.get('total_bytes_estimate'))
    downloaded = valid_number(data.get('downloaded_bytes')) or 0
    fraction = min(1.0, max(0.0, downloaded / total)) if total else None
    speed = valid_number(data.get('speed'))
    eta = valid_number(data.get('eta'))
    remaining = f'{int(eta)//60:02d}:{int(eta)%60:02d}' if eta is not None and eta >= 0 else '—'
    return fraction, f'{human_size(downloaded)} / {human_size(total)}', (human_size(speed) + '/s') if speed else '—', remaining


class DownloadCancelled(Exception):
    """Cancelamento cooperativo solicitado pela interface."""


def check_cancel(cancel_event):
    if cancel_event is not None and cancel_event.is_set():
        raise DownloadCancelled('Download cancelado.')


def download(url, folder, mode, quality, emit, fps="Automático", cancel_event=None):
    """Executa em uma thread; a interface recebe eventos por uma fila."""
    check_cancel(cancel_event)
    from yt_dlp import YoutubeDL

    def hook(data):
        check_cancel(cancel_event)
        if data.get('status') == 'downloading':
            emit('progress', progress_data(data))
        elif data.get('status') == 'finished':
            emit('stage', 'Finalizando etapa de download…')

    def post_hook(data):
        if data.get('status') == 'started':
            check_cancel(cancel_event)
        if data.get('status') in ('started', 'processing'):
            emit('stage', 'Processando o arquivo com FFmpeg…')

    opts = make_options(folder, mode, quality, hook, post_hook, fps=fps)
    emit('stage', 'Buscando informações do vídeo…')
    with YoutubeDL(opts) as ydl:
        check_cancel(cancel_event)
        info = ydl.extract_info(youtube_url(url), download=True)
        if not info:
            raise RuntimeError('O vídeo não retornou informações.')
        emit('done', info.get('title') or 'Vídeo')


def friendly_error(error):
    text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", str(error))
    if "Requested format is not available" in text:
        return "Não há um formato compatível com essa resolução e FPS. Experimente Automático ou outra resolução."
    if re.search(r"\b403\b", text):
        return "O servidor recusou o download (HTTP 403). Tente novamente e confira se o yt-dlp está atualizado: python -m pip install -U yt-dlp[default]"
    lower = text.lower()
    if re.search(r"\b429\b", text):
        return "Muitas solicitações ao servidor (HTTP 429). Tente novamente mais tarde."
    if "private video" in lower or "video unavailable" in lower:
        return "O vídeo está indisponível ou privado. Verifique o link e as permissões."
    if "timed out" in lower or "temporary failure in name resolution" in lower:
        return "Falha de conexão. Verifique sua internet e tente novamente."
    return text
