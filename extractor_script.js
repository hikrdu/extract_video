// Script para extrair títulos e URLs dos vídeos - execute no console do navegador

(function() {
  // Seleciona todos os elementos com classe 'text-title pt-1'
  const titleElements = document.querySelectorAll('h2.text-title.pt-1');
  
  // Seleciona todos os iframes com src contendo 'player.vimeo.com'
  const iframes = document.querySelectorAll('iframe[src*="player.vimeo.com"]');
  
  const videos = [];
  
  // Mapeia cada título com sua URL correspondente
  titleElements.forEach((titleEl, index) => {
    const title = titleEl.textContent.trim();
    
    // Procura o iframe mais próximo
    let url = null;
    
    if (iframes[index]) {
      url = iframes[index].src;
    }
    
    if (title && url) {
      videos.push({
        title: title,
        url: url
      });
    }
  });
  
  // Gera o JSON
  const jsonOutput = JSON.stringify(videos, null, 4);
  
  // Exibe no console
  console.log('=== JSON EXTRAÍDO ===');
  console.log(jsonOutput);
  console.log('=== FIM ===');
  
  // Copia para a área de transferência
  navigator.clipboard.writeText(jsonOutput).then(() => {
    console.log('✓ JSON copiado para a área de transferência!');
  }).catch(err => {
    console.error('Erro ao copiar:', err);
  });
  
  // Retorna os dados para uso posterior
  return videos;
})();
