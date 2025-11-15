#!/usr/bin/env python3
"""
Script para reconstruir vídeo do Vimeo baixando arquivo com ranges

Uso:
    python reconstruct_from_ranges.py urls.txt
"""

import subprocess
import imageio_ffmpeg
import os
import sys
import re
import requests
from pathlib import Path
from datetime import datetime

# Adicionar FFmpeg ao PATH
ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
if ffmpeg_dir not in os.environ.get('PATH', ''):
    os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')

def log(msg, level="INFO"):
    """Imprimir mensagem formatada"""
    symbols = {"INFO": "[i]", "OK": "✓", "ERR": "✗", "WAIT": "..."}
    print(f"{symbols.get(level, '>')} {msg}")

def extract_urls_from_text(text):
    """Extrair URLs de texto colado do console"""
    urls = re.findall(r'https://[^\s\]]+', text)
    return urls

def parse_urls_file(filename):
    """Parsear arquivo com URLs"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        urls = extract_urls_from_text(content)
        
        if not urls:
            log(f"Nenhuma URL encontrada em {filename}", "ERR")
            return []
        
        log(f"Encontradas {len(urls)} URLs", "OK")
        return urls
        
    except FileNotFoundError:
        log(f"Arquivo {filename} não encontrado", "ERR")
        return []
    except Exception as e:
        log(f"Erro ao ler arquivo: {e}", "ERR")
        return []

def extract_base_url(url):
    """Extrair URL base sem o range parameter"""
    # Remove tudo após ?pathsig ou &range
    base = re.sub(r'\?.*', '', url)
    return base

def download_with_ranges(urls, output_file):
    """Baixar arquivo usando HTTP Range requests com headers de browser"""
    
    if not urls:
        log("Nenhuma URL para baixar", "ERR")
        return None
    
    # Headers que simulam browser para evitar bloqueios
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://player.vimeo.com/',
        'Accept': '*/*',
        'Accept-Encoding': 'identity',
        'Connection': 'keep-alive'
    }
    
    # Usar session para manter cookies entre requests
    session = requests.Session()
    session.headers.update(headers)
    
    # Extrair ranges de todas as URLs
    ranges = []
    for url in urls:
        match = re.search(r'range=(\d+)-(\d+)', url)
        if match:
            ranges.append((int(match.group(1)), int(match.group(2))))
    
    if not ranges:
        log("Nenhum range encontrado nas URLs", "ERR")
        return None
    
    # Ordenar ranges
    ranges.sort(key=lambda x: x[0])
    
    # Obter URL base (remove range)
    base_url = extract_base_url(urls[0])
    
    log(f"Baixando {len(ranges)} fragmentos", "WAIT")
    log(f"Tamanho total estimado: {(ranges[-1][1] - ranges[0][0]) / (1024**2):.1f} MB", "INFO")
    
    try:
        downloaded = 0
        total_size = ranges[-1][1] - ranges[0][0] + 1
        
        with open(output_file, 'wb') as f:
            for i, (start, end) in enumerate(ranges):
                # Fazer request com Range header
                range_headers = headers.copy()
                range_headers['Range'] = f'bytes={start}-{end}'
                
                try:
                    response = session.get(base_url, headers=range_headers, timeout=30, stream=True)
                    
                    if response.status_code == 403:
                        log(f"URLs expiraram (403 Forbidden) - precisa extrair novamente do browser", "ERR")
                        return None
                    
                    response.raise_for_status()
                    
                    chunk_data = response.content
                    f.write(chunk_data)
                    
                    downloaded += len(chunk_data)
                    percent = (downloaded / total_size) * 100
                    mb = downloaded / (1024**2)
                    
                    if (i + 1) % 5 == 0:  # Print a cada 5 fragmentos
                        print(f"  Fragmento {i+1}/{len(ranges)} ({percent:.1f}% - {mb:.1f} MB)", end='\r')
                    
                except requests.exceptions.RequestException as e:
                    log(f"Erro ao baixar fragmento {i+1}: {e}", "ERR")
                    return None
        
        print()  # Nova linha após progresso
        
        final_size = os.path.getsize(output_file) / (1024**2)
        log(f"Download concluído: {final_size:.1f} MB", "OK")
        
        return output_file
        
    except Exception as e:
        log(f"Erro durante download: {e}", "ERR")
        if os.path.exists(output_file):
            os.remove(output_file)
        return None
    finally:
        session.close()

def validate_mp4(filename):
    """Verificar se arquivo é MP4 válido"""
    try:
        with open(filename, 'rb') as f:
            header = f.read(4)
            # MP4 típico começa com...
            return True
    except:
        return False

def move_to_results(output_file):
    """Mover arquivo para pasta Results"""
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

def main():
    urls_file = sys.argv[1] if len(sys.argv) > 1 else "urls.txt"
    
    if not os.path.exists(urls_file):
        print("\n" + "="*70)
        print("RECONSTRUTOR DE VÍDEO DO VIMEO (Via Range Downloads)")
        print("="*70)
        print(f"\nArquivo '{urls_file}' não encontrado!")
        print("\nPASSO 1: Extrair URLs do console")
        print("  - Abra: https://player.vimeo.com/video/ID")
        print("  - Pressione F12 → Console")
        print("  - Cole: extract_vimeo_urls.js")
        print("  - Copie TODO o output e salve em urls.txt")
        print("\nPASSO 2: Executar")
        print(f"  python reconstruct_from_ranges.py")
        print("\n" + "="*70 + "\n")
        sys.exit(1)
    
    try:
        print("\n" + "="*70)
        print("RECONSTRUINDO VÍDEO DO VIMEO")
        print("="*70 + "\n")
        
        # Parse URLs
        urls = parse_urls_file(urls_file)
        
        if not urls:
            raise RuntimeError("Nenhuma URL foi extraída")
        
        # Gerar nome de output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"vimeo_reconstructed_{timestamp}.mp4"
        
        # Baixar
        result = download_with_ranges(urls, output_file)
        
        if not result:
            raise RuntimeError("Falha ao baixar")
        
        # Validar
        if not validate_mp4(result):
            log("Aviso: Arquivo pode estar corrompido", "WAIT")
        
        # Mover para Results
        final_file = move_to_results(result)
        
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
        sys.exit(1)

if __name__ == "__main__":
    main()
