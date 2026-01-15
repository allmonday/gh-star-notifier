import { ref, onMounted, onUnmounted } from 'vue'
import { Notify } from 'quasar'
import axios from 'axios'

const API_URL = ''  // Empty string since we're on same origin

export function usePushNotification() {
  const isSupported = ref('serviceWorker' in navigator && 'PushManager' in window)
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

    // If already granted, return true
    if (Notification.permission === 'granted') {
      permission.value = 'granted'
      return true
    }

    // If already denied, show instructions
    if (Notification.permission === 'denied') {
      permission.value = 'denied'
      error.value = 'Notification permission was denied. Please enable it in browser settings.'
      Notify.create({
        type: 'negative',
        message: 'Notification permission denied. Please enable it in browser settings.',
        position: 'top',
        timeout: 5000
      })
      return false
    }

    // Request permission
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

  /**
   * Get VAPID public key from server
   */
  async function getVapidPublicKey() {
    try {
      const response = await axios.get('/api/vapid-public-key')
      vapidPublicKey.value = response.data.publicKey
      console.log('✅ Got VAPID public key')
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
      console.log('🔔 Starting subscription process...')

      // Step 1: Request permission
      console.log('Step 1: Requesting notification permission...')
      const hasPermission = await requestPermission()
      if (!hasPermission) {
        throw new Error('Notification permission denied')
      }

      // Step 2: Register service worker
      console.log('Step 2: Registering service worker...')
      if (!('serviceWorker' in navigator)) {
        throw new Error('Service workers are not supported by this browser')
      }

      const swReg = await navigator.serviceWorker.register('/sw.js')
      console.log('✅ Service Worker registered:', swReg)
      swRegistration.value = swReg

      // Wait for service worker to be ready
      await navigator.serviceWorker.ready
      console.log('✅ Service Worker ready')

      // Get the ready registration
      const readySW = await navigator.serviceWorker.getRegistration()
      console.log('✅ Got ready service worker registration')

      // Step 3: Get VAPID public key
      console.log('Step 3: Getting VAPID public key...')
      const vapidKey = await getVapidPublicKey()

      // Step 4: Subscribe to push
      console.log('Step 4: Subscribing to push notifications...')
      const pushSubscription = await readySW.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidKey)
      })

      console.log('✅ Push subscription created:', pushSubscription)

      // Step 5: Send subscription to server
      console.log('Step 5: Sending subscription to server...')
      await axios.post('/api/subscribe', {
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

      console.log('✅ Subscription complete!')
      return pushSubscription
    } catch (err) {
      console.error('❌ Subscription failed:', err)
      error.value = err.message || 'Subscription failed'

      Notify.create({
        type: 'negative',
        message: `Subscription failed: ${err.message}`,
        position: 'top',
        timeout: 5000
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
