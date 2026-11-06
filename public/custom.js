// Script personalizzato per forzare l'aggiornamento immediato di Favicon e Logo
(function() {
    function refreshFavicon() {
        const head = document.head || document.getElementsByTagName('head')[0];
        
        // Rimuove eventuali tag icon precedenti
        const existingLinks = document.querySelectorAll("link[rel*='icon']");
        existingLinks.forEach(el => el.remove());

        // Crea il nuovo link per la favicon PNG ad alta risoluzione con cache-buster
        const newLink = document.createElement('link');
        newLink.rel = 'icon';
        newLink.type = 'image/png';
        newLink.href = '/public/favicon.png?v=' + Date.now();
        head.appendChild(newLink);

        const shortcutLink = document.createElement('link');
        shortcutLink.rel = 'shortcut icon';
        shortcutLink.type = 'image/png';
        shortcutLink.href = '/public/favicon.png?v=' + Date.now();
        head.appendChild(shortcutLink);
    }

    function refreshLogo() {
        const logos = document.querySelectorAll('img[alt="logo"], img.logo');
        logos.forEach(img => {
            if (img.src && !img.src.includes('cb=')) {
                const sep = img.src.includes('?') ? '&' : '?';
                img.src = img.src + sep + 'cb=' + Date.now();
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            refreshFavicon();
            refreshLogo();
        });
    } else {
        refreshFavicon();
        refreshLogo();
    }

    // Osserva l'albero DOM per intercettare il logo quando React lo renderizza
    const observer = new MutationObserver(() => {
        refreshLogo();
    });
    observer.observe(document.body, { childList: true, subtree: true });
})();
