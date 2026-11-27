"""VDownload — interface gráfica em Tkinter."""
import os
import sys
import queue
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from downloader import (VIDEO_QUALITIES, AUDIO_QUALITIES, FPS_OPTIONS, friendly_error, youtube_url,
                        missing_dependencies, download)

BG = '#11131B'
PANEL = '#1B1E29'
FIELD = '#141720'
BORDER = '#35394B'
TEXT = '#F3EFFA'
MUTED = '#A9AABC'
PINK = '#DDA5F5'
ACCENT = '#DDA5F5'
FONT = 'Segoe UI' if sys.platform == 'win32' else 'DejaVu Sans'


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('VDownload — YouTube')
        self.geometry('1000x680')
        self.minsize(900, 650)
        self.configure(bg=BG)
        self.events = queue.Queue()
        self.busy = False
        self.mode = tk.StringVar(value='MP4')
        self.quality = tk.StringVar(value='1080p')
        self.fps = tk.StringVar(value='Automático')
        default = Path.home() / 'Downloads'
        self.folder = tk.StringVar(value=str(default if default.is_dir() else Path.home()))
        self.url = tk.StringVar()
        self.status = tk.StringVar(value='Pronto para baixar')
        self.details = tk.StringVar(value='Cole um link para começar.')
        self.percent = tk.StringVar(value='—')
        self.size = tk.StringVar(value='—')
        self.speed = tk.StringVar(value='—')
        self.eta = tk.StringVar(value='—')
        self._style()
        self._build()
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.after(100, self.process_events)
