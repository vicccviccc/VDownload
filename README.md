# VDownload 2.1

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

## Novidades da versão 2.1

- Preferências de formato, resolução, FPS e pasta são salvas localmente.
- Histórico dos últimos 100 downloads concluídos, com opção de reutilizar links ou apagar o histórico.
- Cancelamento cooperativo durante o download. Uma operação de rede ou conversão já em andamento pode precisar terminar antes de responder ao cancelamento. Arquivos parciais podem permanecer para retomada.
- Download automático opcional de novos links copiados do YouTube. A opção começa desligada em cada sessão e exige confirmação. O aplicativo ignora o link que já estava copiado ao ativar a função e não enfileira links copiados durante outro download.

Os dados são gravados apenas no computador: em `%LOCALAPPDATA%/VDownload` no Windows ou `~/.local/share/VDownload` no Linux (respeitando `XDG_DATA_HOME`). A área de transferência só é monitorada quando a opção está ativa; textos que não sejam links válidos não são guardados nem enviados. Use somente conteúdo autorizado.

## Testes

```powershell
python -m unittest discover -s tests -v
```

Os testes unitários não baixam vídeos reais. A interface e os downloads da versão 2.1 ainda precisam de validação manual no Windows e Linux.

## Estrutura do projeto

- `app.py`: interface gráfica e controle dos eventos.
- `downloader.py`: validação, formatos e integração com yt-dlp.
- `storage.py`: preferências e histórico em JSON.
- `clipboard_watch.py`: identificação de novos links copiados.
- `tests/`: testes unitários que não dependem do YouTube.
