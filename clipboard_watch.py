"""Identifica novos links copiados, apenas enquanto a opção estiver ligada."""
from downloader import youtube_url


class ClipboardWatcher:
    def __init__(self):
        self.previous = None

    @staticmethod
    def canonical(text):
        if not isinstance(text, str):
            return None
        try:
            return youtube_url(text)
        except ValueError:
            return None

    def reset(self, text):
        # o link que já estava copiado antes de ativar não inicia download
        self.previous = self.canonical(text)

    def observe(self, text, busy=False):
        current = self.canonical(text)
        changed = current != self.previous
        self.previous = current
        return current if current and changed and not busy else None
