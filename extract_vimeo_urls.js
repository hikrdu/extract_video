/**
 * EXTRATOR UNIFICADO DE URLs DO VIMEO
 * 
 * Cole este script TODO NO CONSOLE (F12) enquanto o vídeo está sendo reproduzido
 * Ele vai tentar TODOS os métodos para encontrar as URLs de vídeo
 */

(async function extractVimeoURLs() {
    console.log("\n" + "=".repeat(70));
    console.log("EXTRATOR UNIFICADO DE URLs DO VIMEO");
    console.log("=".repeat(70) + "\n");
    
    let allURLs = new Set();
    
    // ====== MÉTODO 1: Performance API (requisições já feitas) ======
    console.log("[1/5] Verificando requisições da Performance API...");
    const resources = performance.getEntriesByType('resource');
    const videoPatterns = [
        r => r.name.includes('mp4'),
        r => r.name.includes('.m4v'),
        r => r.name.includes('avf'),
        r => r.name.includes('vod-adaptive'),
        r => r.name.includes('/v2/range/')
    ];
    
    resources.forEach(resource => {
        if (videoPatterns.some(pattern => pattern(resource))) {
            allURLs.add(resource.name);
        }
    });
    console.log(`  Encontradas: ${allURLs.size} URLs\n`);
    
    // ====== MÉTODO 2: Interceptar XMLHttpRequest ======
    console.log("[2/5] Monitorando XMLHttpRequest...");
    const originalXHROpen = XMLHttpRequest.prototype.open;
    let xhrCount = 0;
    
    XMLHttpRequest.prototype.open = function(method, url) {
        if (url && videoPatterns.some(p => p({name: url}))) {
            allURLs.add(url);
            xhrCount++;
        }
        return originalXHROpen.apply(this, arguments);
    };
    console.log(`  Pronto para monitorar. Continue reproduzindo...\n`);
    
    // ====== MÉTODO 3: Interceptar Fetch ======
    console.log("[3/5] Monitorando Fetch API...");
    const originalFetch = window.fetch;
    let fetchCount = 0;
    
    window.fetch = async function(...args) {
        const url = args[0]?.toString?.();
        if (url && videoPatterns.some(p => p({name: url}))) {
            allURLs.add(url);
            fetchCount++;
            console.log(`  📹 Fetch: ${url.substring(0, 60)}...`);
        }
        return originalFetch.apply(this, args);
    };
    console.log(`  Pronto para monitorar. Continue reproduzindo...\n`);
    
    // ====== MÉTODO 4: Cache API ======
    console.log("[4/5] Verificando Cache Storage...");
    let cacheCount = 0;
    try {
        const cacheNames = await caches.keys();
        for (let cacheName of cacheNames) {
            const cache = await caches.open(cacheName);
            const requests = await cache.keys();
            for (let req of requests) {
                if (videoPatterns.some(p => p({name: req.url}))) {
                    allURLs.add(req.url);
                    cacheCount++;
                }
            }
        }
        console.log(`  Encontradas: ${cacheCount} URLs no cache\n`);
    } catch(e) {
        console.log(`  Sem acesso ao cache: ${e.message}\n`);
    }
    
    // ====== MÉTODO 5: Procurar manifestos ======
    console.log("[5/5] Verificando manifestos (MPD/M3U8)...");
    let manifestCount = 0;
    resources.forEach(resource => {
        if (resource.name.includes('.mpd') || 
            resource.name.includes('.m3u8') || 
            resource.name.includes('master') ||
            resource.name.includes('variant')) {
            allURLs.add(resource.name);
            manifestCount++;
        }
    });
    console.log(`  Encontradas: ${manifestCount} manifestos\n`);
    
    // ====== RESULTADO FINAL ======
    console.log("=".repeat(70));
    console.log(`RESULTADO: ${allURLs.size} URLs ENCONTRADAS`);
    console.log("=".repeat(70) + "\n");
    
    // Separar por tipo
    const videoURLs = Array.from(allURLs).filter(u => u.includes('mp4'));
    const audioURLs = Array.from(allURLs).filter(u => u.includes('audio'));
    const otherURLs = Array.from(allURLs).filter(u => !u.includes('mp4') && !u.includes('audio'));
    
    if (videoURLs.length > 0) {
        console.log("📹 VÍDEO (sem áudio):");
        videoURLs.forEach((url, i) => console.log(`  [${i}] ${url}`));
        console.log();
    }
    
    if (audioURLs.length > 0) {
        console.log("🔊 ÁUDIO:");
        audioURLs.forEach((url, i) => console.log(`  [${i}] ${url}`));
        console.log();
    }
    
    if (otherURLs.length > 0) {
        console.log("📋 OUTROS (manifestos, etc):");
        otherURLs.slice(0, 5).forEach((url, i) => console.log(`  [${i}] ${url.substring(0, 80)}...`));
        if (otherURLs.length > 5) console.log(`  ... e mais ${otherURLs.length - 5}`);
        console.log();
    }
    
    // ====== COPIAR PARA CLIPBOARD ======
    const urlList = Array.from(allURLs).join('\n');
    try {
        await navigator.clipboard.writeText(urlList);
        console.log("✓ Todas as URLs copiadas para clipboard!\n");
    } catch(e) {
        console.log("Não foi possível copiar para clipboard\n");
    }
    
    // ====== INSTRUÇÕES FINAIS ======
    console.log("=".repeat(70));
    console.log("PRÓXIMOS PASSOS:");
    console.log("=".repeat(70));
    console.log("\n1. Procure pelos URLs acima que tem VIDEO e AUDIO");
    console.log("2. Copie ambos os URLs");
    console.log("3. Use o script 'merge_from_urls.py' para mesclar:\n");
    console.log("   python merge_from_urls.py <video_url> <audio_url>\n");
    console.log("Ou, se tiver apenas 1 URL com vídeo+áudio:");
    console.log("   python merge_from_urls.py <url_completa>\n");
    
    // ====== FUNÇÃO DE SUPORTE ======
    window.copyVideoURL = function(index) {
        const urls = Array.from(allURLs);
        if (urls[index]) {
            navigator.clipboard.writeText(urls[index]);
            console.log(`✓ Copiado: ${urls[index]}`);
        }
    };
    console.log("Dica: Use copyVideoURL(n) para copiar uma URL específica");
    console.log("Exemplo: copyVideoURL(0)\n");
    
    return Array.from(allURLs);
})();
