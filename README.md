# extract_video

Ferramenta simples para baixar vídeos do Vimeo (com áudio) e salvar como MP4, usando `yt-dlp` e `ffmpeg` (via `imageio_ffmpeg`). Os arquivos finais são salvos em `Results/` com o nome do título fornecido.

## Requisitos
- Python 3.8+
- Pacotes Python:
  - `yt-dlp`
  - `imageio-ffmpeg`
- Opcional para `--impersonate` (pode melhorar compatibilidade em alguns casos):
  - `curl_cffi`, `brotli`, `certifi`

Instalação rápida dos pacotes:

```bash
python -m pip install -U yt-dlp imageio-ffmpeg
# Opcional para impersonation:
python -m pip install -U curl_cffi brotli certifi
```

## Uso (lote via JSON)
- Estrutura esperada do arquivo JSON: `[{"title": "Nome do vídeo", "url": "https://..."}, ...]`
- Arquivo de exemplo: `video_ids.example.json` (copie e edite como `video_ids.json`)

Crie seu arquivo a partir do exemplo:

```bash
cp video_ids.example.json video_ids.json
# edite o video_ids.json com seus títulos e URLs
```

Com cookies (recomendado para evitar 401/Unauthorized em vídeos privados/protegidos):

```bash
python download_and_merge.py --json video_ids.json --cookies cookies.txt
```

Se os vídeos estiverem embutidos numa página específica, informe o Referer:

```bash
python download_and_merge.py --json video_ids.json \
  --cookies cookies.txt \
  --referer "https://pagina-que-embedda-os-videos.example"
```

Impersonation (opcional, requer pacotes adicionais instalados acima):

```bash
python download_and_merge.py --json video_ids.json --cookies cookies.txt --impersonate chrome
```

## Como obter `cookies.txt`
- Use uma extensão como “Get cookies.txt LOCALLY” (Chrome/Edge/Firefox) para exportar cookies no formato Netscape.
- Salve o arquivo como `cookies.txt` na raiz do projeto.
- Exporte cookies para o domínio que realmente guarda o acesso (ex.: `vimeo.com` ou o site que integra o player).

## Saída e nomes de arquivo
- Cada item do JSON é salvo em `Results/` com o `title` como nome do arquivo `.mp4`.
- O título é sanitizado para ser compatível com Windows.
- Se já existir um arquivo com o mesmo nome, é adicionado um sufixo com timestamp para evitar sobrescrita.

## Script principal
- `download_and_merge.py` — baixa vídeo e áudio com `yt-dlp`, mescla com `ffmpeg` e move para `Results/`.

## Estrutura mínima do projeto
```
.
├─ download_and_merge.py
├─ video_ids.json
├─ Results/
├─ README.md
└─ LICENSE
```

## Dicas de resolução de problemas
- 401/Unauthorized: use `--cookies cookies.txt` e, se necessário, `--referer` apontando à página que contém o player.
- Aviso sobre “impersonation”: instale os pacotes opcionais e rode com `--impersonate chrome`.
- Se o site exigir login, garanta que o `cookies.txt` foi exportado da sua sessão autenticada.
