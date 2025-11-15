#!/usr/bin/env python3
"""
Script para baixar de Vimeo e mesclar vídeo + áudio automaticamente.

Melhorias:
- Usa o Python atual (sys.executable) para chamar yt-dlp.
- Suporta Referer, cookies do navegador e cookies.txt (corrige 401/Unauthorized).
- Define User-Agent moderno e tenta formatos padrão (evita IDs hardcoded).
- Faz retry automático com cookies do navegador (Chrome/Edge/Firefox) se falhar.
- Mensagens de erro mais úteis e saída final na pasta Results/.

Uso rápido:
    python download_and_merge.py <video_url> [--referer URL] \
            [--cookies-from-browser chrome|edge|firefox] [--cookies cookies.txt] \
            [--ua UA_STRING] [--quality 1080|720|best]

Exemplos:
    python download_and_merge.py https://player.vimeo.com/video/12345 \
        --referer https://site-que-embedda-o-player.com/pagina
    python download_and_merge.py https://vimeo.com/12345 --cookies-from-browser chrome
"""

import subprocess
import imageio_ffmpeg
import os
import sys
import argparse
import json
import shutil
from pathlib import Path
from datetime import datetime

# Adicionar FFmpeg ao PATH
ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
if ffmpeg_dir not in os.environ.get('PATH', ''):
    os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')

def log(msg, level="INFO"):
    symbols = {"INFO": "[i]", "OK": "[OK]", "ERR": "[ERROR]", "WAIT": "..."}
    print(f"{symbols.get(level, '>')} {msg}")

DEFAULT_UA = (
    # Chrome 120 on Windows 10 64-bit
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _build_base_cmd(args):
    """Constroi os argumentos base do yt-dlp conforme opções fornecidas."""
    py = sys.executable or "python"
    cmd = [py, "-m", "yt_dlp", "--no-warnings", "--no-progress", "-N", "8"]

    # User-Agent padrão (pode ser sobrescrito)
    ua = args.ua or os.environ.get("VIMEO_UA") or DEFAULT_UA
    cmd += ["--user-agent", ua]

    # Referer ajuda muito em Vimeo embed/hotlink-protection
    referer = args.referer or os.environ.get("VIMEO_REFERER")
    if referer:
        cmd += ["--referer", referer]

    # Cookies do navegador (preferível) ou arquivo cookies.txt
    if args.cookies_from_browser:
        cmd += ["--cookies-from-browser", args.cookies_from_browser]
    elif args.cookies and os.path.exists(args.cookies):
        cmd += ["--cookies", args.cookies]

    # Impersonate (opcional). Use apenas se usuário pedir/ambientar dependências
    impersonate = args.impersonate or os.environ.get("VIMEO_IMPERSONATE")
    if impersonate:
        cmd += ["--impersonate", impersonate]

    return cmd


def _run(cmd):
    """Executa um comando e retorna (returncode, stdout, stderr)."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def _try_with_browsers(base_cmd, fmt_args, out_file):
    """Tenta baixar usando cookies de navegadores comuns, em ordem."""
    for browser in ("chrome", "edge", "firefox"):
        log(f"Tentando com cookies do navegador: {browser}", "WAIT")
        cmd = base_cmd.copy()
        # Remover qualquer cookies anterior
        while "--cookies-from-browser" in cmd:
            i = cmd.index("--cookies-from-browser")
            del cmd[i : i + 2]
        while "--cookies" in cmd:
            i = cmd.index("--cookies")
            del cmd[i : i + 2]
        cmd += ["--cookies-from-browser", browser]
        cmd += fmt_args + ["-o", out_file]
        rc, _, err = _run(cmd)
        if rc == 0 and os.path.exists(out_file) and os.path.getsize(out_file) > 0:
            return True, err
        # Mostra última parte do erro para diagnóstico
        if err:
            print(err[-400:])
    return False, None


def download_vimeo(video_url, args):
    """Baixar vídeo e áudio com yt-dlp, com opções e retries."""
    
    print("\n" + "="*70)
    print("DOWNLOAD + MESCLA VIMEO (HD + ÁUDIO)")
    print("="*70 + "\n")
    
    log(f"URL: {video_url}", "INFO")
    log("Baixando vídeo (HD)...", "WAIT")
    
    base_cmd = _build_base_cmd(args)

    # Preferir MP4 (evita Matroska) e vídeo-only
    video_fmt = (
        "bv*[ext=mp4][vcodec!=none]"
        "/bv*[protocol^=https][vcodec!=none]"
        "/best[vcodec!=none]"
    )
    video_args = ["-f", video_fmt, video_url]

    # Executa tentativa principal
    cmd_video = base_cmd + video_args + ["-o", "temp_video.mp4"]
    rc_v, _, err_v = _run(cmd_video)
    
    if rc_v != 0 or not os.path.exists('temp_video.mp4'):
        log("Falha inicial no vídeo. Tentando alternativas...", "ERR")
        if err_v:
            print(err_v[-500:])
        # Retry com cookies dos navegadores mais comuns
        ok, _ = _try_with_browsers(base_cmd, video_args, "temp_video.mp4")
        if not ok:
            log("Erro ao baixar vídeo após tentativas", "ERR")
            return None, None
    
    if not os.path.exists('temp_video.mp4'):
        log("Arquivo de vídeo não criado", "ERR")
        return None, None
    
    size_mb = os.path.getsize('temp_video.mp4') / (1024**2)
    log(f"Vídeo baixado: {size_mb:.1f} MB", "OK")
    
    # Baixar ÁUDIO
    log("Baixando áudio...", "WAIT")
    
    audio_fmt = "ba[ext=m4a]/bestaudio[acodec!=none]/bestaudio"
    audio_args = ["-f", audio_fmt, video_url]

    cmd_audio = base_cmd + audio_args + ["-o", "temp_audio.mp4"]
    rc_a, _, err_a = _run(cmd_audio)
    
    if rc_a != 0 or not os.path.exists('temp_audio.mp4'):
        log("Falha inicial no áudio. Tentando alternativas...", "ERR")
        if err_a:
            print(err_a[-500:])
        ok, _ = _try_with_browsers(base_cmd, audio_args, "temp_audio.mp4")
        if not ok:
            log("Erro ao baixar áudio. Prosseguindo apenas com vídeo", "ERR")
            return 'temp_video.mp4', None
    
    if not os.path.exists('temp_audio.mp4'):
        log("Arquivo de áudio não criado", "ERR")
        return 'temp_video.mp4', None
    
    size_mb = os.path.getsize('temp_audio.mp4') / (1024**2)
    log(f"Áudio baixado: {size_mb:.1f} MB", "OK")
    
    return 'temp_video.mp4', 'temp_audio.mp4'

def _sanitize_filename(name: str, fallback_prefix: str = "vimeo") -> str:
    """Sanitize a string to be a safe Windows filename, return with .mp4 extension."""
    if not name:
        name = f"{fallback_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    # Remove/replace illegal characters for Windows: <>:"/\|?*
    bad = '<>:"/\\|?*'
    trans = {ord(c): '_' for c in bad}
    cleaned = name.translate(trans).strip().rstrip('.')
    # Collapse spaces
    cleaned = ' '.join(cleaned.split())
    # Limit length reasonably
    if len(cleaned) > 180:
        cleaned = cleaned[:180].rstrip()
    if not cleaned.lower().endswith('.mp4'):
        cleaned += '.mp4'
    return cleaned


def merge_video_audio(video_file, audio_file, title: str | None = None):
    """Mesclar vídeo e áudio com FFmpeg"""
    
    if not video_file or not os.path.exists(video_file):
        log("Arquivo de vídeo não encontrado", "ERR")
        return None
    
    desired_name = _sanitize_filename(title or "") if title else None

    if not audio_file or not os.path.exists(audio_file):
        log("Arquivo de áudio não encontrado - usando apenas vídeo", "WAIT")
        if desired_name:
            output_file = desired_name
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"vimeo_video_only_{timestamp}.mp4"
        shutil.copy(video_file, output_file)
        return output_file
    
    if desired_name:
        output_file = desired_name
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"vimeo_merged_{timestamp}.mp4"
    
    log(f"Mesclando vídeo + áudio → {output_file}", "WAIT")
    
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    
    cmd = [
        ffmpeg,
        '-i', video_file,
        '-i', audio_file,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-y',
        output_file
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0 and os.path.exists(output_file):
        final_size = os.path.getsize(output_file) / (1024**3)
        log(f"Mescla concluída: {final_size:.2f} GB", "OK")
        return output_file
    else:
        log("Erro ao mesclar", "ERR")
        if result.stderr:
            print(result.stderr[-500:])
        return None

def move_to_results(output_file, preferred_name: str | None = None):
    """Mover arquivo para pasta Results"""
    if not output_file or not os.path.exists(output_file):
        return None
    
    results_dir = os.path.join(os.getcwd(), "Results")
    os.makedirs(results_dir, exist_ok=True)
    
    final_name = os.path.basename(output_file)
    if preferred_name:
        safe_preferred = _sanitize_filename(preferred_name)
        final_name = safe_preferred
    final_path = os.path.join(results_dir, final_name)

    # Avoid overwrite
    if os.path.exists(final_path):
        stem, ext = os.path.splitext(final_name)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_path = os.path.join(results_dir, f"{stem}_{ts}{ext}")
    
    try:
        shutil.move(output_file, final_path)
        log(f"Arquivo movido: Results/{os.path.basename(output_file)}", "OK")
        return final_path
    except Exception as e:
        log(f"Erro ao mover: {e}", "ERR")
        return output_file

def cleanup():
    """Remover arquivos temporários"""
    for file in ['temp_video.mp4', 'temp_audio.mp4']:
        try:
            if os.path.exists(file):
                os.remove(file)
        except:
            pass


def _process_single(video_url: str, args, title: str | None = None) -> tuple[bool, str | None]:
    """Processa um único vídeo: baixa, mescla e move para Results.
    Retorna (ok, caminho_final_ou_None)."""
    # Baixar vídeo e áudio
    video_file, audio_file = download_vimeo(video_url, args)
    if not video_file:
        return False, None

    # Mesclar
    merged_file = merge_video_audio(video_file, audio_file, title)
    if not merged_file:
        return False, None

    # Mover para Results com nome do título (se houver)
    final_file = move_to_results(merged_file, preferred_name=title if title else None)
    # Limpeza local
    cleanup()
    return bool(final_file and os.path.exists(final_file)), final_file

def main():
    parser = argparse.ArgumentParser(
        description="Baixa vídeo + áudio de Vimeo e mescla em MP4"
    )
    parser.add_argument("video_url", nargs='?', help="URL do vídeo (vimeo.com ou player.vimeo.com)")
    parser.add_argument("--json", dest="json_file", help="Arquivo JSON com [{title, url}] para download em lote")
    parser.add_argument("--referer", help="URL da página que embedda o player (corrige 401)")
    parser.add_argument(
        "--cookies-from-browser",
        dest="cookies_from_browser",
        choices=["chrome", "edge", "firefox"],
        help="Usa cookies da sessão do navegador"
    )
    parser.add_argument("--cookies", help="Caminho para cookies.txt (Netscape format)")
    parser.add_argument("--ua", help="User-Agent a ser usado (opcional)")
    parser.add_argument(
        "--impersonate",
        help="yt-dlp --impersonate (ex: chrome). Requer dependências opcionais do yt-dlp.")
    parser.add_argument(
        "--quality",
        choices=["1080", "720", "best"],
        default="best",
        help="Preferência de qualidade (apenas indicativo; seleção é por formato)"
    )

    args = parser.parse_args()
    video_url = args.video_url
    
    try:
        # Checagem básica: yt_dlp instalado?
        try:
            __import__("yt_dlp")
        except Exception:
            raise RuntimeError(
                "yt-dlp não encontrado. Instale com: pip install -U yt-dlp"
            )

        # Modo JSON (lote)
        if args.json_file:
            jf = Path(args.json_file)
            if not jf.exists():
                raise RuntimeError(f"JSON não encontrado: {jf}")
            with open(jf, 'r', encoding='utf-8') as f:
                try:
                    items = json.load(f)
                    if not isinstance(items, list):
                        raise ValueError("JSON deve ser uma lista de objetos {title,url}")
                except Exception as je:
                    raise RuntimeError(f"Erro lendo JSON: {je}")

            ok_count = 0
            fail = []
            for idx, item in enumerate(items, start=1):
                title = (item.get('title') or '').strip()
                url = (item.get('url') or '').strip()
                if not url:
                    log(f"Item {idx} inválido (sem url)", "ERR")
                    fail.append((idx, title, url))
                    continue
                log(f"Processando {idx}/{len(items)}: {title or url}", "INFO")
                ok, final_file = _process_single(url, args, title=title)
                if ok:
                    ok_count += 1
                    log(f"OK → {final_file}", "OK")
                else:
                    fail.append((idx, title, url))

            print("\n" + "="*70)
            print(f"FINALIZADO: {ok_count} OK / {len(fail)} com erro(s)")
            if fail:
                print("Falhas:")
                for idx, title, url in fail:
                    print(f" - #{idx}: {title or '(sem título)'} | {url}")
            print("="*70 + "\n")
        else:
            # Único vídeo (URL posicional)
            if not video_url:
                raise RuntimeError("Forneça uma URL ou um arquivo --json")
            ok, final_file = _process_single(video_url, args)
            if not ok:
                raise RuntimeError("Falha ao processar vídeo")

            print("\n" + "="*70)
            print("CONCLUÍDO COM SUCESSO!")
            print("="*70)
            print(f"\nArquivo final: {final_file}")
            
            if os.path.exists(final_file):
                size_mb = os.path.getsize(final_file) / (1024**2)
                size_gb = size_mb / 1024
                if size_gb >= 1:
                    print(f"Tamanho: {size_gb:.2f} GB")
                else:
                    print(f"Tamanho: {size_mb:.1f} MB")
            
            print("\n" + "="*70 + "\n")
        
    except Exception as e:
        print(f"\n[ERRO] {e}\n")
        print(
            "Dicas: se receber 401/Unauthorized em Vimeo, tente adicionar --referer "
            "(a página que contém o player) ou usar --cookies-from-browser chrome.\n"
            "Caso veja aviso sobre 'impersonation', instale dependências opcionais do yt-dlp "
            "(ex.: pip install curl_cffi brotli certifi) e rode com --impersonate chrome."
        )
        cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()
