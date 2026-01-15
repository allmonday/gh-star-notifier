import { ref, onMounted, onUnmounted } from 'vue'
import { Notify } from 'quasar'
import axios from 'axios'

const API_URL = import.meta.env.API_URL || ''

export function usePushNotification() {
  const subscription = ref(null)
  const isSubscribed = ref(false)
  const permission = ref('default')
  const vapidPublicKey = ref('')
  const loading = ref(false)
  const error = ref(null)
  const swRegistration = ref(null)

  /**
   * Convert base64 string to Uint8Array
   */
  function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
    const base64 = (base64String + padding)
      .replace(/\-/g, '+')
      .replace(/_/g, '/')

    const rawData = window.atob(base64)
    const outputArray = new Uint8Array(rawData.length)

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i)
    }
    return outputArray
  }

  /**
   * Request notification permission
   */
  async function requestPermission() {
    if (!('Notification' in window)) {
      error.value = 'This browser does not support notifications'
      return false
    }

    if (Notification.permission === 'granted') {
      permission.value = 'granted'
      return true
    }

    if (Notification.permission !== 'denied') {
      const result = await Notification.requestPermission()
      permission.value = result

      if (result === 'granted') {
        Notify.create({
          type: 'positive',
          message: 'Notification permission granted',
          position: 'top'
        })
        return true
      } else {
        Notify.create({
          type: 'warning',
          message: 'Notification permission denied',
          position: 'top'
        })
        return false
      }
    }

    permission.value = 'denied'
    return false
  }

  /**
   * Get VAPID public key from server
   */
  async function getVapidPublicKey() {
    try {
      const response = await axios.get(`${API_URL}/api/vapid-public-key`)
      vapidPublicKey.value = response.data.publicKey
      return response.data.publicKey
    } catch (err) {
      console.error('❌ Error getting VAPID key:', err)
      error.value = 'Failed to get VAPID key'
      throw err
    }
  }

  /**
   * Register Service Worker
   */
  async function registerServiceWorker() {
    if (!('serviceWorker' in navigator)) {
      error.value = 'Service workers are not supported by this browser'
      throw new Error('Service worker not supported')
    }

    try {
      const registration = await navigator.serviceWorker.register('/sw.js')
      console.log('✅ Service Worker registered:', registration)
      swRegistration.value = registration

      // Wait for service worker to be ready
      await navigator.serviceWorker.ready
      console.log('✅ Service Worker ready')

      return registration
    } catch (err) {
      console.error('❌ Service Worker registration failed:', err)
      error.value = 'Service Worker registration failed'
      throw err
    }
  }

  /**
   * Subscribe to push notifications
   */
  async function subscribe() {
    loading.value = true
    error.value = null

    try {
      // Step 1: Request permission
      const hasPermission = await requestPermission()
      if (!hasPermission) {
        throw new Error('Notification permission denied')
      }

      // Step 2: Register service worker
      const registration = await registerServiceWorker()

      // Step 3: Get VAPID public key
      const vapidKey = await getVapidPublicKey()

      // Step 4: Subscribe to push
      const pushSubscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidKey)
      })

      console.log('✅ Push subscription created:', pushSubscription)

      // Step 5: Send subscription to server
      await axios.post(`${API_URL}/api/subscribe`, {
        subscription: pushSubscription.toJSON()
      })

      subscription.value = pushSubscription.toJSON()
      isSubscribed.value = true

      Notify.create({
        type: 'positive',
        message: 'Successfully subscribed to push notifications',
        position: 'top',
        timeout: 3000
      })

      return pushSubscription
    } catch (err) {
      console.error('❌ Subscription failed:', err)
      error.value = err.message || 'Subscription failed'

      Notify.create({
        type: 'negative',
        message: `Subscription failed: ${err.message}`,
        position: 'top'
      })

      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Unsubscribe from push notifications
   */
  async function unsubscribe() {
    loading.value = true
    error.value = null

    try {
      if (!swRegistration.value) {
        throw new Error('No service worker registration')
      }

      const pushSubscription = await swRegistration.value.pushManager.getSubscription()
      if (!pushSubscription) {
        isSubscribed.value = false
        subscription.value = null
        return
      }

      // Unsubscribe from push service
      await pushSubscription.unsubscribe()

      // Notify server
      await axios.post(`${API_URL}/api/unsubscribe`, {
        subscription: pushSubscription.toJSON()
      })

      subscription.value = null
      isSubscribed.value = false

      Notify.create({
        type: 'info',
        message: 'Unsubscribed from push notifications',
        position: 'top'
      })
    } catch (err) {
      console.error('❌ Unsubscribe failed:', err)
      error.value = err.message || 'Unsubscribe failed'

      Notify.create({
        type: 'negative',
        message: `Unsubscribe failed: ${err.message}`,
        position: 'top'
      })

      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Check current subscription status
   */
  async function checkSubscriptionStatus() {
    try {
      if (!('serviceWorker' in navigator)) {
        return false
      }

      const registration = await navigator.serviceWorker.ready
      const pushSubscription = await registration.pushManager.getSubscription()

      if (pushSubscription) {
        subscription.value = pushSubscription.toJSON()
        isSubscribed.value = true
        return true
      } else {
        isSubscribed.value = false
        subscription.value = null
        return false
      }
    } catch (err) {
      console.error('❌ Error checking subscription status:', err)
      return false
    }
  }

  /**
   * Send test notification
   */
  async function sendTestNotification(title = 'Test Notification', body = 'This is a test notification') {
    loading.value = true
    error.value = null

    try {
      await axios.post(`${API_URL}/api/test-notification`, {
        title,
        body
      })

      Notify.create({
        type: 'positive',
        message: 'Test notification sent',
        position: 'top'
      })
    } catch (err) {
      console.error('❌ Test notification failed:', err)
      error.value = err.message || 'Failed to send test notification'

      Notify.create({
        type: 'negative',
        message: `Failed to send test notification: ${err.message}`,
        position: 'top'
      })

      throw err
    } finally {
      loading.value = false
    }
  }

  // Check subscription status on mount
  onMounted(async () => {
    permission.value = Notification.permission
    await checkSubscriptionStatus()
  })

  return {
    subscription,
    isSubscribed,
    permission,
    vapidPublicKey,
    loading,
    error,
    subscribe,
    unsubscribe,
    checkSubscriptionStatus,
    sendTestNotification
  }
}
