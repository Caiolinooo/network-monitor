/**
 * sw.js - Service Worker para o Monitor de Rede
 * Autor: Caio Valerio Goulart Correia
 * Versão: 1.0.0
 */

// Nome do cache
const CACHE_NAME = 'network-monitor-cache-v1';

// Arquivos a serem armazenados em cache
const CACHE_ASSETS = [
    '/',
    '/static/css/styles.css',
    '/static/css/themes.css',
    '/static/js/theme.js',
    '/static/js/main.js',
    '/static/js/pwa.js',
    '/static/js/chart.min.js',
    '/static/icons/favicon.ico',
    '/static/icons/logo.png',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    '/static/manifest.json'
];

// Instalação do Service Worker
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Cache aberto');
                return cache.addAll(CACHE_ASSETS);
            })
            .then(() => self.skipWaiting())
    );
});

// Ativação do Service Worker
self.addEventListener('activate', event => {
    // Limpa caches antigos
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Removendo cache antigo:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Estratégia de cache: Network First, fallback para cache
self.addEventListener('fetch', event => {
    // Ignora requisições não GET
    if (event.request.method !== 'GET') return;

    // Ignora requisições de API
    if (event.request.url.includes('/api/')) {
        // Para chamadas API, tenta rede e retorna resposta offline personalizada
        event.respondWith(
            fetch(event.request)
                .catch(() => {
                    return new Response(JSON.stringify({
                        success: false,
                        error: 'Você está offline. Algumas funcionalidades podem estar indisponíveis.',
                        offline: true
                    }), {
                        headers: { 'Content-Type': 'application/json' }
                    });
                })
        );
        return;
    }

    // Para arquivos estáticos e página principal
    event.respondWith(
        fetch(event.request)
            .then(response => {
                // Cria clone da resposta
                const responseClone = response.clone();
                
                // Abre o cache e armazena a resposta
                caches.open(CACHE_NAME)
                    .then(cache => {
                        cache.put(event.request, responseClone);
                    });
                
                return response;
            })
            .catch(() => {
                // Tenta buscar do cache se a rede falhar
                return caches.match(event.request)
                    .then(cachedResponse => {
                        if (cachedResponse) {
                            return cachedResponse;
                        }
                        
                        // Se não estiver no cache e for HTML, retorna página offline
                        if (event.request.headers.get('accept').includes('text/html')) {
                            return caches.match('/');
                        }
                        
                        // Caso contrário, falha
                        return new Response('Falha ao carregar o recurso enquanto offline.', {
                            status: 503,
                            headers: { 'Content-Type': 'text/plain' }
                        });
                    });
            })
    );
});

// Evento push para notificações
self.addEventListener('push', event => {
    const data = event.data.json();
    
    const options = {
        body: data.body || 'Atualização do Monitor de Rede',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/badge-72x72.png',
        data: {
            url: data.url || '/'
        }
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title || 'Monitor de Rede', options)
    );
});

// Evento de clique em notificação
self.addEventListener('notificationclick', event => {
    event.notification.close();
    
    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});