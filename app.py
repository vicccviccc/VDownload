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

    def _style(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('Dark.TCombobox', fieldbackground=FIELD, background=PANEL,
                        foreground=TEXT, arrowcolor=TEXT, bordercolor=BORDER,
                        lightcolor=BORDER, darkcolor=BORDER, padding=8,
                        font=(FONT, 11))
        style.map('Dark.TCombobox', fieldbackground=[('readonly', FIELD)],
                  foreground=[('readonly', TEXT)])
        self.option_add('*TCombobox*Listbox.background', FIELD)
        self.option_add('*TCombobox*Listbox.foreground', TEXT)
        self.option_add('*TCombobox*Listbox.selectBackground', ACCENT)
        style.configure('Pink.Horizontal.TProgressbar', troughcolor=FIELD,
                        background=PINK, bordercolor=FIELD, lightcolor=PINK,
                        darkcolor=PINK, thickness=9)

    def label(self, parent, text=None, *, variable=None, size=11, color=TEXT,
              weight='normal', bg=None, **kwargs):
        return tk.Label(parent, text=text or '', textvariable=variable,
                        bg=bg or parent.cget('bg'), fg=color, font=(FONT, size, weight), **kwargs)

    def button(self, parent, text, command, primary=False, **kwargs):
        return tk.Button(parent, text=text, command=command,
                         bg=ACCENT if primary else PANEL, fg=BG if primary else TEXT,
                         activebackground='#C58ADE' if primary else BORDER,
                         activeforeground=BG if primary else TEXT, disabledforeground='#888d98',
                         relief='flat', bd=0, padx=18, pady=7, cursor='hand2',
                         font=(FONT, 11, 'bold'), **kwargs)

    def entry(self, parent, variable, readonly=False):
        return tk.Entry(parent, textvariable=variable, font=(FONT, 12), bg=FIELD,
                        fg=TEXT, insertbackground=TEXT, relief='flat', bd=0,
                        highlightthickness=1, highlightcolor=PINK, highlightbackground=BORDER,
                        readonlybackground=FIELD, state='readonly' if readonly else 'normal')

    def _build(self):
        outer = tk.Frame(self, bg=BG, padx=28, pady=24)
        outer.pack(fill='both', expand=True)
        top = tk.Frame(outer, bg=BG)
        top.pack(fill='x')
        self.label(top, ' V ', size=21, weight='bold', color=BG, bg=PINK).pack(side='left', ipady=4)
        brand = tk.Frame(top, bg=BG)
        brand.pack(side='left', padx=12)
        self.label(brand, 'VDownload', size=19, weight='bold').pack(anchor='w')
        self.label(brand, 'DESKTOP / 2.0', size=9, color=MUTED).pack(anchor='w')
        self.label(top, 'YouTube · MP4 / MP3', size=10, color=MUTED).pack(side='right')
        tk.Frame(outer, bg=BORDER, height=1).pack(fill='x', pady=(16, 16))
        self.label(outer, 'Novo download', size=25, weight='bold').pack(anchor='w')
        self.label(outer, 'Configure o arquivo antes de baixar.', color=MUTED).pack(anchor='w', pady=(2, 18))
        body = tk.Frame(outer, bg=BG)
        body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=5, uniform='panels')
        body.columnconfigure(1, weight=3, uniform='panels')
        body.rowconfigure(0, weight=1)
        card = tk.Frame(body, bg=PANEL, padx=19, pady=18, highlightthickness=1, highlightbackground=BORDER)
        card.grid(row=0, column=0, sticky='nsew', padx=(0, 16))
        def heading(text):
            self.label(card, text, color=PINK, size=10, weight='bold').pack(anchor='w', pady=(0, 7))
        heading('01   LINK DO VÍDEO')
        link = tk.Frame(card, bg=PANEL)
        link.pack(fill='x', pady=(0, 15))
        self.link_entry = self.entry(link, self.url)
        self.link_entry.pack(side='left', fill='x', expand=True, ipady=8, padx=(0, 8))
        self.link_entry.bind('<Return>', lambda _e: self.start())
        self.paste_button = self.button(link, 'Colar', self.paste)
        self.paste_button.pack(side='right')
        heading('02   FORMATO')
        format_row = tk.Frame(card, bg=PANEL)
        format_row.pack(fill='x', pady=(0, 14))
        self.mode_buttons = []
        for mode, name in [('MP4', 'MP4 · Vídeo'), ('MP3', 'MP3 · Áudio')]:
            button = tk.Radiobutton(format_row, text=name, variable=self.mode, value=mode,
                command=self.change_format, indicatoron=False, selectcolor='#433450',
                bg=FIELD, fg=TEXT, activebackground=BORDER, activeforeground=TEXT,
                relief='flat', bd=0, font=(FONT, 11, 'bold'), pady=9)
            button.pack(side='left', fill='x', expand=True, padx=(0, 5))
            self.mode_buttons.append(button)
        options = tk.Frame(card, bg=PANEL)
        options.pack(fill='x', pady=(0, 15))
        for i in range(2): options.columnconfigure(i, weight=1, uniform='option')
        left = tk.Frame(options, bg=PANEL)
        left.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        self.quality_label = self.label(left, 'Resolução', weight='bold')
        self.quality_label.pack(anchor='w')
        self.combo = ttk.Combobox(left, textvariable=self.quality, values=VIDEO_QUALITIES, state='readonly', style='Dark.TCombobox', width=12)
        self.combo.pack(fill='x', pady=(6, 0))
        right = tk.Frame(options, bg=PANEL)
        right.grid(row=0, column=1, sticky='ew')
        self.label(right, 'Taxa de quadros', weight='bold').pack(anchor='w')
        self.fps_combo = ttk.Combobox(right, textvariable=self.fps, values=FPS_OPTIONS, state='readonly', style='Dark.TCombobox', width=12)
        self.fps_combo.pack(fill='x', pady=(6, 0))
        heading('03   DESTINO')
        folder_row = tk.Frame(card, bg=PANEL)
        folder_row.pack(fill='x')
        self.entry(folder_row, self.folder, readonly=True).pack(side='left', fill='x', expand=True, ipady=8, padx=(0, 8))
        self.folder_button = self.button(folder_row, 'Alterar', self.choose_folder)
        self.folder_button.pack(side='right')
        self.download_button = self.button(card, 'Baixar arquivo', self.start, primary=True)
        self.download_button.pack(side='bottom', fill='x', pady=(16, 0), ipady=5)
        progress_panel = tk.Frame(body, bg=PANEL, padx=19, pady=18, highlightthickness=1, highlightbackground=BORDER)
        progress_panel.grid(row=0, column=1, sticky='nsew')
        self.label(progress_panel, 'ATIVIDADE', color=PINK, weight='bold', size=10).pack(anchor='w')
        self.label(progress_panel, variable=self.status, weight='bold', size=16, wraplength=275, justify='left').pack(anchor='w', pady=(18, 5))
        self.label(progress_panel, variable=self.details, color=MUTED, size=10, wraplength=275, justify='left').pack(anchor='w')
        self.progress = ttk.Progressbar(progress_panel, maximum=100, style='Pink.Horizontal.TProgressbar')
        self.progress.pack(fill='x', pady=(23, 7))
        self.label(progress_panel, variable=self.percent, weight='bold', color=PINK).pack(anchor='w')
        metrics = tk.Frame(progress_panel, bg=PANEL)
        metrics.pack(fill='x', pady=(18, 0))
        for i, (name, var) in enumerate([('Dados', self.size), ('Velocidade', self.speed), ('Tempo restante', self.eta)]):
            cell = tk.Frame(metrics, bg=PANEL)
            cell.grid(row=i//2, column=i%2, sticky='nw', pady=(0, 16), padx=(0, 12))
            self.label(cell, name, color=MUTED, size=9).pack(anchor='w')
            self.label(cell, variable=var, size=11, weight='bold').pack(anchor='w')
        self.button(progress_panel, 'Abrir pasta de destino', self.open_folder).pack(side='bottom', fill='x', ipady=5)
        bottom = tk.Frame(outer, bg=BG)
        bottom.pack(fill='x', pady=(16, 0))
        self.label(bottom, 'Baixe apenas conteúdo autorizado.', color=MUTED, size=9).pack(side='left')
        self.label(bottom, 'Python / yt-dlp', color=MUTED, size=9).pack(side='right')
        self.link_entry.focus_set()

    def paste(self):
        try:
            self.url.set(self.clipboard_get().strip())
        except tk.TclError:
            messagebox.showinfo('Área de transferência', 'Nenhum texto encontrado.')

    def choose_folder(self):
        selected = filedialog.askdirectory(initialdir=self.folder.get())
        if selected:
            self.folder.set(selected)

    def open_folder(self):
        folder = self.folder.get()
        try:
            if sys.platform == 'win32':
                os.startfile(folder)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', folder])
            else:
                subprocess.Popen(['xdg-open', folder])
        except OSError as error:
            messagebox.showerror('Erro', str(error))

    def change_format(self):
        audio = self.mode.get() == 'MP3'
        self.combo.configure(values=AUDIO_QUALITIES if audio else VIDEO_QUALITIES)
        self.quality.set('192 kbps' if audio else '1080p')
        self.quality_label.configure(text='Qualidade do áudio' if audio else 'Resolução')
        self.fps_combo.configure(state='disabled' if audio else 'readonly')

    def set_busy(self, busy):
        self.busy = busy
        for widget in [self.link_entry, self.paste_button, self.folder_button,
                       self.download_button, *self.mode_buttons]:
            widget.configure(state='disabled' if busy else 'normal')
        self.combo.configure(state='disabled' if busy else 'readonly')
        self.fps_combo.configure(state='disabled' if busy or self.mode.get() == 'MP3' else 'readonly')
        self.download_button.configure(text='Baixando…' if busy else 'Baixar arquivo  ↓')

    def start(self):
        if self.busy:
            return
        try:
            url = youtube_url(self.url.get())
        except ValueError as error:
            messagebox.showwarning('Link inválido', str(error))
            return
        missing = missing_dependencies()
        if missing:
            messagebox.showerror('Dependências pendentes', '\n\n'.join(missing) + '\n\nVeja o README para instalar.')
            return
        if not Path(self.folder.get()).is_dir():
            messagebox.showwarning('Pasta inválida', 'Escolha uma pasta de destino válida.')
            return
        self.set_busy(True)
        self.progress['value'] = 0
        self.percent.set('—')
        self.size.set('—')
        self.speed.set('—')
        self.eta.set('—')
        args = url, self.folder.get(), self.mode.get(), self.quality.get(), self.fps.get()
        threading.Thread(target=self.worker, args=args, daemon=True).start()

    def worker(self, url, folder, mode, quality, fps):
        # A thread de download nunca altera widgets diretamente.
        try:
            download(url, folder, mode, quality, fps=fps, emit=lambda kind, data: self.events.put((kind, data)))
        except Exception as error:
            self.events.put(('error', friendly_error(error)))

    def process_events(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == 'stage':
                    self.status.set(data)
                    self.percent.set('—')
                    self.details.set('Aguarde a próxima etapa.')
                    self.progress.stop()
                    self.progress.configure(mode='indeterminate')
                    self.progress.start(12)
                elif kind == 'progress':
                    fraction, size, speed, eta = data
                    self.status.set('Baixando mídia…')
                    self.details.set('Progresso da etapa atual (vídeo ou áudio).')
                    if fraction is not None:
                        self.progress.stop()
                        self.progress.configure(mode='determinate', value=fraction * 100)
                        self.percent.set(f'{fraction * 100:.0f}%')
                    else:
                        if str(self.progress['mode']) != 'indeterminate':
                            self.progress.configure(mode='indeterminate')
                            self.progress.start(12)
                        self.percent.set('—')
                    self.size.set(size)
                    self.speed.set(speed)
                    self.eta.set(eta)
                elif kind in ('done', 'error'):
                    self.progress.stop()
                    self.progress.configure(mode='determinate', value=100 if kind == 'done' else 0)
                    self.set_busy(False)
                    self.speed.set('—')
                    self.eta.set('—')
                    if kind == 'done':
                        self.status.set('Download concluído!')
                        self.percent.set('100%')
                        self.details.set(f'{data} — salvo na pasta escolhida.')
                    else:
                        self.status.set('Não foi possível baixar')
                        self.percent.set('—')
                        self.details.set('Confira a mensagem de erro e tente novamente.')
                        messagebox.showerror('Falha no download', data)
        except queue.Empty:
            pass
        self.after(100, self.process_events)

    def close(self):
        if self.busy:
            messagebox.showinfo('Download em andamento', 'Aguarde o download terminar antes de fechar o aplicativo.')
            return
        self.destroy()


if __name__ == '__main__':
    App().mainloop()
