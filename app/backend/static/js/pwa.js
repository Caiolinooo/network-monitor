/**
 * pwa.js - Script para suporte a PWA (Progressive Web App)
 * Autor: Caio Valerio Goulart Correia
 * Versão: 1.0.0
 */

(function() {
    // Registra o service worker para PWA
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', function() {
            navigator.serviceWorker.register('/static/sw.js')
                .then(function(registration) {
                    console.log('Service Worker registrado com sucesso:', registration.scope);
                })
                .catch(function(error) {
                    console.log('Falha ao registrar Service Worker:', error);
                });
        });
    }

    // Evento para instalação da PWA
    let deferredPrompt;
    const installButton = document.createElement('button');
    installButton.style.display = 'none';
    installButton.classList.add('pwa-install-btn');
    installButton.textContent = 'Instalar Aplicativo';
    document.body.appendChild(installButton);

    window.addEventListener('beforeinstallprompt', (e) => {
        // Previne o comportamento padrão
        e.preventDefault();
        // Guarda o evento para usar mais tarde
        deferredPrompt = e;
        // Torna o botão visível
        installButton.style.display = 'block';
    });

    installButton.addEventListener('click', (e) => {
        // Esconde o botão
        installButton.style.display = 'none';
        // Mostra o prompt
        deferredPrompt.prompt();
        // Espera o usuário responder ao prompt
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('Usuário aceitou a instalação da PWA');
            } else {
                console.log('Usuário negou a instalação da PWA');
            }
            deferredPrompt = null;
        });
    });
    
    // Esconde o botão se já estiver instalado
    window.addEventListener('appinstalled', (evt) => {
        installButton.style.display = 'none';
        console.log('PWA instalada com sucesso');
    });

    // Detecta se está sendo executado como PWA instalada
    if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true) {
        document.body.classList.add('pwa-mode');
        console.log('Aplicação rodando em modo standalone (PWA)');
    }
})();