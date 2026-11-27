# VDownload 2.0

Aplicativo desktop em Python para baixar vídeos ou áudio do YouTube quando autorizado. Interface feita com Tkinter e baseada no [design do Figma](https://www.figma.com/design/IUDsW72Rh4VusCWsoogI4N?node-id=1-2).

## Executar no Windows

Requer Python 3.10+, FFmpeg e Deno. Se já instalou as duas ferramentas na versão anterior, não precisa instalar novamente.

```powershell
winget install --id Gyan.FFmpeg -e --source winget
winget install --id DenoLand.Deno -e --source winget
```

Reabra o terminal e confira se as dependências estão disponíveis:

```powershell
python --version
ffmpeg -version
ffprobe -version
deno --version
```

Se algum comando não for reconhecido, verifique a instalação e o PATH do Windows.

Caso ainda não tenha o projeto, faça o download pelo botão **Code → Download ZIP** e extraia os arquivos, ou clone com Git:

```powershell
git clone https://github.com/vicccviccc/VDownload.git
cd VDownload
```

Execute os seguintes comandos na pasta do projeto:

```powershell
python -m pip install -U -r requirements.txt
python app.py
```

## Opções

- MP4: até 2160p, dependendo dos formatos disponíveis. A resolução é um limite máximo.
- FPS: automático, 30 (inclui 29,97) ou 60 (inclui 59,94). As opções explícitas não interpolam quadros nem retornam automaticamente outra taxa; se não houver formato compatível, escolha outra resolução ou Automático.
- MP3: 128, 192 ou 320 kbps. O seletor de FPS fica desativado.
- Pasta de destino, progresso por etapa, velocidade e tempo restante.

Se ocorrer HTTP 403, atualize a biblioteca com `python -m pip install -U "yt-dlp[default]"`. Use apenas conteúdo cujo download seja autorizado.

## Testes

```powershell
python -m unittest discover -s tests -v
```

Interface verificada em Linux; download real e execução no Windows não verificados nesta versão.

## Estrutura do projeto

- `app.py`: interface gráfica e controle dos eventos.
- `downloader.py`: validação, formatos e integração com yt-dlp.
- `tests/`: testes unitários que não dependem do YouTube.
