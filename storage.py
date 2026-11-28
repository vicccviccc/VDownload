"""Preferências e histórico locais do VDownload, sem acesso à rede."""
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from datetime import datetime

from downloader import VIDEO_QUALITIES, AUDIO_QUALITIES, FPS_OPTIONS, youtube_url

MAX_HISTORY = 100


def data_dir():
    if os.name == 'nt':
        return Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'VDownload'
    return Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local/share') / 'VDownload'


def read_json(path, fallback):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return fallback


def write_json(path, value):
    """Grava primeiro em arquivo temporário, preservando o anterior em caso de erro."""
    path = Path(path)
    temp = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                delete=False) as handle:
            temp = Path(handle.name)
            json.dump(value, handle, ensure_ascii=False, indent=2)
        temp.replace(path)
        return True
    except (OSError, ValueError, TypeError):
        return False
    finally:
        if temp is not None:
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass


def normalize_preferences(raw):
    raw = raw if isinstance(raw, dict) else {}
    mode = 'MP3' if raw.get('mode') == 'MP3' else 'MP4'
    choices = AUDIO_QUALITIES if mode == 'MP3' else VIDEO_QUALITIES
    quality = raw.get('quality')
    if quality not in choices:
        quality = '192 kbps' if mode == 'MP3' else '1080p'
    fps = raw.get('fps')
    if fps not in FPS_OPTIONS:
        fps = 'Automático'
    folder = raw.get('folder')
    if isinstance(folder, str):
        try:
            valid = Path(folder).is_dir()
        except (OSError, ValueError):
            valid = False
    else:
        valid = False
    if not valid:
        downloads = Path.home() / 'Downloads'
        folder = str(downloads if downloads.is_dir() else Path.home())
    return {'mode': mode, 'quality': quality, 'fps': fps, 'folder': folder}


class LocalStore:
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory is not None else data_dir()

    def preferences(self):
        return normalize_preferences(read_json(self.directory / 'preferences.json', {}))

    def save_preferences(self, values):
        return write_json(self.directory / 'preferences.json', normalize_preferences(values))

    def history(self):
        raw = read_json(self.directory / 'history.json', [])
        if not isinstance(raw, list):
            return []
        entries = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            keys = ('title', 'url', 'mode', 'quality', 'folder', 'date')
            if not all(isinstance(item.get(key), str) for key in keys):
                continue
            if item['mode'] not in ('MP3', 'MP4'):
                continue
            try:
                url = youtube_url(item['url'])
            except ValueError:
                continue
            entries.append({**{key: item[key] for key in keys}, 'url': url})
            if len(entries) >= MAX_HISTORY:
                break
        return entries

    def record(self, title, url, mode, quality, folder):
        entry = {
            'title': str(title), 'url': youtube_url(url), 'mode': mode,
            'quality': quality, 'folder': str(folder),
            'date': datetime.now().astimezone().isoformat(timespec='seconds'),
        }
        return write_json(self.directory / 'history.json',
                          [entry, *self.history()][:MAX_HISTORY])

    def clear_history(self):
        return write_json(self.directory / 'history.json', [])
