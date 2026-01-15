/* eslint-disable no-undef */
import { precacheAndRoute } from 'workbox-precaching/precacheAndRoute'

precacheAndRoute(self.__WB_MANIFEST)

// Push notification event
self.addEventListener('push', function(event) {
  console.log('📩 Push event received:', event)

  let data = {
    title: 'GitHub Star Notifier',
    body: 'You have a new notification',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png'
  }

  if (event.data) {
    try {
      const payload = event.data.json()
      data = {
        ...data,
        ...payload
      }
      console.log('📦 Push payload:', payload)
    } catch (error) {
      console.error('❌ Error parsing push data:', error)
    }
  }

  const options = {
    body: data.body,
    icon: data.icon || '/icons/icon-192x192.png',
    badge: data.badge || '/icons/badge-72x72.png',
    image: data.image,
    vibrate: [200, 100, 200],
    data: {
      url: data.url || '/'
    },
    actions: [
      {
        action: 'open',
        title: 'Open',
        icon: '/icons/action-open.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/icons/action-close.png'
      }
    ]
  }

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  )
})

// Notification click event
self.addEventListener('notificationclick', function(event) {
  console.log('🔔 Notification clicked:', event)

  event.notification.close()

  if (event.action === 'close') {
    return
  }

  // Default action: open the URL
  const url = event.notification.data?.url || '/'

  event.waitUntil(
    clients.matchAll({ type: 'window' }).then(function(clientList) {
      // If a window is already open, focus it
      for (const client of clientList) {
        if (client.url === url && 'focus' in client) {
          return client.focus()
        }
      }
      // Otherwise, open a new window
      if (clients.openWindow) {
        return clients.openWindow(url)
      }
    })
  )
})

// Notification close event
self.addEventListener('notificationclose', function(event) {
  console.log('🔕 Notification closed:', event)
})
