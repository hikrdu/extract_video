# Download de Vídeos do Vimeo com Áudio e Vídeo

Guia completo para baixar vídeos do Vimeo com áudio e vídeo sincronizados.

## ⚡ Quick Start (Método Recomendado)

```bash
python download_and_merge.py "https://player.vimeo.com/video/ID"
```


Substitua `ID` pelo número do vídeo do Vimeo. **Pronto!** O vídeo será baixado em HD com áudio e salvo em `Results/`.

---

## 📋 Pré-requisitos

- Python 3.13+
- Navegador web (Chrome, Firefox, Safari, Edge)
- Pasta de destino: `Results/`

---

## 🎯 Passo a Passo Detalhado

### PASSO 1: Instalar Dependências (Primeira vez apenas)

```bash
pip install yt-dlp imageio-ffmpeg requests
```

### PASSO 2: Executar o Script Principal

```bash
python download_and_merge.py "https://player.vimeo.com/video/745586627"
```

**O que acontece automaticamente:**
1. ✅ Baixa vídeo em HD (1080p se disponível, senão 720p)
2. ✅ Baixa áudio em alta qualidade
3. ✅ Mescla vídeo + áudio com FFmpeg
4. ✅ Salva em `Results/vimeo_merged_YYYYMMDD_HHMMSS.mp4`
5. ✅ Remove arquivos temporários

---

## 📁 Estrutura de Arquivos

```
Desktop/test/
├── download_and_merge.py        ← Script principal (USE ESTE)
├── extract_vimeo_urls.js        ← Para casos especiais (ver abaixo)
├── Results/
│   ├── vimeo_merged_20251114_195143.mp4
│   ├── vimeo_merged_20251115_120532.mp4
│   └── [seus vídeos aqui]
└── .venv/                       ← Ambiente virtual Python
```

---

## 🔧 Scripts Disponíveis

### 1. `download_and_merge.py` ⭐ RECOMENDADO

**Uso:** Método mais simples e direto

```bash
python download_and_merge.py "https://player.vimeo.com/video/ID"
```

**Saída:** Vídeo com áudio em `Results/`

**Quando usar:** 99% dos casos

---

### 2. `extract_vimeo_urls.js` (Para Casos Especiais)

**Uso:** Se o script Python falhar, use extração manual

**Passos:**
1. Abra: `https://player.vimeo.com/video/ID`
2. Pressione **F12** → aba **Console**
3. Cole o conteúdo de `extract_vimeo_urls.js` inteiro
4. Deixe reproduzindo por 10-15 segundos
5. Copie as URLs do console
6. Salve em `urls.txt`

```bash
python reconstruct_from_ranges.py urls.txt
```

**Quando usar:** Quando `download_and_merge.py` não funcionar (raro)

---

## 🎬 Exemplos de Uso

### Exemplo 1: Vídeo Simples

```bash
python download_and_merge.py "https://player.vimeo.com/video/745586627"
```

**Output:**
```
======================================================================
DOWNLOAD + MESCLA VIMEO (HD + ÁUDIO)
======================================================================

[i] URL: https://player.vimeo.com/video/745586627
... Baixando vídeo (HD)...
✓ Vídeo baixado: 447.2 MB
... Baixando áudio...
✓ Áudio baixado: 171.5 MB
... Mesclando vídeo + áudio → vimeo_merged_20251115_120532.mp4
✓ Mescla concluída: 0.62 GB
✓ Arquivo movido: Results/vimeo_merged_20251115_120532.mp4

======================================================================
CONCLUÍDO COM SUCESSO!
======================================================================

Arquivo final: C:\Users\ricardo.nunes\Desktop\test\Results\vimeo_merged_20251115_120532.mp4
Tamanho: 0.62 GB

======================================================================
```

### Exemplo 2: Loop para Múltiplos Vídeos

```bash
python download_and_merge.py "https://player.vimeo.com/video/745586627" && \
python download_and_merge.py "https://player.vimeo.com/video/745587672" && \
python download_and_merge.py "https://player.vimeo.com/video/745587673"
```

---

## 🐛 Solução de Problemas

### Problema: "Error: format not available"

**Solução:** O script tenta formatos em cascata. Se falhar, espere 1 hora e tente novamente (servidor pode estar temporariamente instável).

### Problema: "403 Forbidden" (URLs expiradas)

**Solução:** Use `extract_vimeo_urls.js` novamente para gerar URLs frescas.

### Problema: Vídeo sem áudio

**Solução:** O vídeo foi salvo sem áudio. Isto é raro. Use:
```bash
python download_and_merge.py "https://player.vimeo.com/video/ID"
```

### Problema: FFmpeg não encontrado

**Solução:** 
```bash
pip install --upgrade imageio-ffmpeg
```

---

## 📊 Formatos Suportados

| Resolução | Bitrate | Tamanho (2h) |
|-----------|---------|-------------|
| 1080p     | 837 kbps| ~700 MB     |
| 720p      | 559 kbps| ~470 MB     |
| 540p      | 373 kbps| ~307 MB     |
| 360p      | 248 kbps| ~204 MB     |

**Áudio:** AAC estéreo, 128 kbps

---

## ⚙️ Configuração Avançada

### Alterar Qualidade de Áudio

Edite `download_and_merge.py`, linha com `'-b:a'`:

```python
'-b:a', '192k',  # Aumentar para 192k (melhor qualidade)
```

### Usar Codec Diferente

Para compatibilidade com navegadores antigos:

```python
'-c:a', 'libmp3lame',  # MP3 em vez de AAC
'-b:a', '128k',
```

---

## 📝 Notas Importantes

1. **Tempo de Download:** Depende da velocidade da internet (Vimeo serve em ~5 Mbps)
2. **Espaço em Disco:** Garanta ~2 GB livres (download + merging temporário)
3. **Licença:** Respeite os direitos autorais dos vídeos
4. **Múltiplos Downloads:** Execute um de cada vez (evita congestionamento)

---

## 📞 Suporte

Se tiver problemas:

1. Verifique se Python está na versão 3.13+:
   ```bash
   python --version
   ```

2. Verifique se yt-dlp está atualizado:
   ```bash
   python -m yt_dlp --version
   ```

3. Verifique se FFmpeg está acessível:
   ```bash
   python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"
   ```

---

## 📦 Limpeza de Arquivos Temporários

Se houver `temp_video.mp4` ou `temp_audio.mp4` na pasta:

```bash
rm temp_*.mp4
```

Ou manualmente delete-os.

---

**Última atualização:** 15 de Novembro de 2025

**Status:** ✅ Testado e funcionando com sucesso
