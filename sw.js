self.addEventListener('push', function(event) {
    if (event.data) {
        try {
            const data = event.data.json();
            const title = data.title || 'Notificación Mágica ✨';
            const options = {
                body: data.body || '¡Tienes una nueva actualización en Lunita!',
                icon: data.icon || '/icon-192x192.png',
                badge: data.badge || '/icon-192x192.png',
                vibrate: [200, 100, 200],
                data: {
                    url: '/'
                }
            };
            event.waitUntil(self.registration.showNotification(title, options));
        } catch(e) {
            console.error("Error parseando push data:", e);
        }
    }
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then(windowClients => {
            for (let i = 0; i < windowClients.length; i++) {
                const client = windowClients[i];
                if (client.url === '/' && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow('/');
            }
        })
    );
});
