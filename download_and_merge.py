#!/usr/bin/env python3
"""
Script para baixar Vimeo e mesclar vídeo + áudio automaticamente
"""

import subprocess
import imageio_ffmpeg
import os
import sys
from pathlib import Path
from datetime import datetime

# Adicionar FFmpeg ao PATH
ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
if ffmpeg_dir not in os.environ.get('PATH', ''):
    os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')

def log(msg, level="INFO"):
    symbols = {"INFO": "[i]", "OK": "✓", "ERR": "✗", "WAIT": "..."}
    print(f"{symbols.get(level, '>')} {msg}")

def download_vimeo(video_url):
    """Baixar vídeo com yt-dlp"""
    
    print("\n" + "="*70)
    print("DOWNLOAD + MESCLA VIMEO (HD + ÁUDIO)")
    print("="*70 + "\n")
    
    log(f"URL: {video_url}", "INFO")
    log("Baixando vídeo (HD)...", "WAIT")
    
    # Baixar VÍDEO em HD
    cmd_video = [
        'python', '-m', 'yt_dlp',
        '-f', 'hls-fastly_skyfire-837/hls-fastly_skyfire-559/hls-fastly_skyfire-373/best[vcodec!=none]',
        '-o', 'temp_video.mp4',
        video_url
    ]
    
    result = subprocess.run(cmd_video, capture_output=True, text=True)
    
    if result.returncode != 0:
        log("Erro ao baixar vídeo", "ERR")
        print(result.stderr[-500:])
        return None, None
    
    if not os.path.exists('temp_video.mp4'):
        log("Arquivo de vídeo não criado", "ERR")
        return None, None
    
    size_mb = os.path.getsize('temp_video.mp4') / (1024**2)
    log(f"Vídeo baixado: {size_mb:.1f} MB", "OK")
    
    # Baixar ÁUDIO
    log("Baixando áudio...", "WAIT")
    
    cmd_audio = [
        'python', '-m', 'yt_dlp',
        '-f', 'hls-fastly_skyfire-audio-high-Original/hls-fastly_skyfire-audio-low-Original/bestaudio[acodec!=none]',
        '-o', 'temp_audio.mp4',
        video_url
    ]
    
    result = subprocess.run(cmd_audio, capture_output=True, text=True)
    
    if result.returncode != 0:
        log("Erro ao baixar áudio", "ERR")
        print(result.stderr[-500:])
        return 'temp_video.mp4', None
    
    if not os.path.exists('temp_audio.mp4'):
        log("Arquivo de áudio não criado", "ERR")
        return 'temp_video.mp4', None
    
    size_mb = os.path.getsize('temp_audio.mp4') / (1024**2)
    log(f"Áudio baixado: {size_mb:.1f} MB", "OK")
    
    return 'temp_video.mp4', 'temp_audio.mp4'

def merge_video_audio(video_file, audio_file):
    """Mesclar vídeo e áudio com FFmpeg"""
    
    if not video_file or not os.path.exists(video_file):
        log("Arquivo de vídeo não encontrado", "ERR")
        return None
    
    if not audio_file or not os.path.exists(audio_file):
        log("Arquivo de áudio não encontrado - usando apenas vídeo", "WAIT")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"vimeo_video_only_{timestamp}.mp4"
        import shutil
        shutil.copy(video_file, output_file)
        return output_file
    
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

def move_to_results(output_file):
    """Mover arquivo para pasta Results"""
    if not output_file or not os.path.exists(output_file):
        return None
    
    results_dir = os.path.join(os.getcwd(), "Results")
    os.makedirs(results_dir, exist_ok=True)
    
    final_path = os.path.join(results_dir, os.path.basename(output_file))
    
    try:
        import shutil
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

def main():
    if len(sys.argv) < 2:
        print("\n" + "="*70)
        print("DOWNLOAD + MESCLA VIMEO (COM ÁUDIO)")
        print("="*70)
        print("\nUso:")
        print("  python download_and_merge.py <video_url>")
        print("\nExemplo:")
        print("  python download_and_merge.py https://player.vimeo.com/video/745587672")
        print("\n" + "="*70 + "\n")
        sys.exit(1)
    
    video_url = sys.argv[1]
    
    try:
        # Baixar vídeo e áudio
        video_file, audio_file = download_vimeo(video_url)
        
        if not video_file:
            raise RuntimeError("Falha ao baixar vídeo")
        
        # Mesclar
        merged_file = merge_video_audio(video_file, audio_file)
        
        if not merged_file:
            raise RuntimeError("Falha ao mesclar")
        
        # Mover para Results
        final_file = move_to_results(merged_file)
        
        # Limpeza
        cleanup()
        
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
        cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()
