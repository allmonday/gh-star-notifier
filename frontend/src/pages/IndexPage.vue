<template>
  <q-page padding>
    <div class="container q-mx-auto" style="max-width: 800px">
      <!-- Header -->
      <div class="text-center q-mb-xl">
        <div class="text-h4 text-weight-bold q-mb-sm">
          <q-icon name="star" size="md" color="yellow" />
          GitHub Star Notifier
        </div>
        <div class="text-body1 text-grey-7">
          Receive push notifications when your repositories are starred
        </div>
      </div>

      <!-- Subscription Status Card -->
      <q-card class="q-mb-md">
        <q-card-section>
          <div class="text-h6">
            <q-icon
              :name="isSubscribed ? 'notifications_active' : 'notifications_off'"
              :color="isSubscribed ? 'positive' : 'grey-6'"
              class="q-mr-sm"
            />
            Subscription Status
          </div>
        </q-card-section>

        <q-card-section>
          <div class="row items-center q-gutter-md">
            <div class="col">
              <q-badge
                :color="subscriptionStatus.color"
                :label="subscriptionStatus.label"
                size="md"
              />
            </div>
            <div class="col-auto">
              <span class="text-body2 text-grey-7">
                Permission: <strong>{{ permission }}</strong>
              </span>
            </div>
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn
            v-if="!isSubscribed"
            unelevated
            color="primary"
            :loading="loading"
            :disable="permission === 'denied'"
            @click="handleSubscribe"
          >
            <q-icon name="notifications" class="q-mr-sm" />
            Subscribe to Notifications
          </q-btn>

          <q-btn
            v-else
            unelevated
            color="negative"
            :loading="loading"
            @click="handleUnsubscribe"
          >
            <q-icon name="notifications_off" class="q-mr-sm" />
            Unsubscribe
          </q-btn>
        </q-card-actions>
      </q-card>

      <!-- Test Notification Card -->
      <q-card class="q-mb-md" v-if="isSubscribed">
        <q-card-section>
          <div class="text-h6">
            <q-icon name="send" color="blue" class="q-mr-sm" />
            Send Test Notification
          </div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="handleSendTest">
            <q-input
              v-model="testTitle"
              label="Title"
              outlined
              dense
              class="q-mb-md"
              :rules="[val => !!val || 'Title is required']"
            />

            <q-input
              v-model="testBody"
              label="Message"
              outlined
              dense
              type="textarea"
              rows="3"
              class="q-mb-md"
              :rules="[val => !!val || 'Message is required']"
            />

            <q-btn
              type="submit"
              unelevated
              color="blue"
              :loading="loading"
            >
              <q-icon name="send" class="q-mr-sm" />
              Send Test Notification
            </q-btn>
          </q-form>
        </q-card-section>
      </q-card>

      <!-- Info Card -->
      <q-card>
        <q-card-section>
          <div class="text-h6">
            <q-icon name="info" color="info" class="q-mr-sm" />
            How it works
          </div>
        </q-card-section>

        <q-card-section>
          <q-list separator>
            <q-item>
              <q-item-section avatar>
                <q-icon name="looks_one" color="primary" />
              </q-item-section>
              <q-item-section>
                <q-item-label>Click "Subscribe to Notifications"</q-item-label>
                <q-item-label caption>
                  Grant permission to receive push notifications
                </q-item-label>
              </q-item-section>
            </q-item>

            <q-item>
              <q-item-section avatar>
                <q-icon name="looks_two" color="primary" />
              </q-item-section>
              <q-item-section>
                <q-item-label>Configure GitHub Webhook</q-item-label>
                <q-item-label caption>
                  Add webhook to your repository settings
                </q-item-label>
              </q-item-section>
            </q-item>

            <q-item>
              <q-item-section avatar>
                <q-icon name="looks_3" color="primary" />
              </q-item-section>
              <q-item-section>
                <q-item-label>Receive Notifications</q-item-label>
                <q-item-label caption>
                  Get notified when someone stars your repository
                </q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>

        <q-card-section>
          <div class="text-subtitle2 q-mb-sm">Webhook Configuration:</div>
          <q-input
            :model-value="webhookUrl"
            outlined
            dense
            readonly
            class="q-mb-sm"
          >
            <template v-slot:append>
              <q-btn
                flat
                dense
                icon="content_copy"
                @click="copyWebhookUrl"
              />
            </template>
          </q-input>
          <div class="text-caption text-grey-7">
            Content type: <code>application/json</code><br>
            Events: <code>Stars</code> → <code>Watch events</code>
          </div>
        </q-card-section>
      </q-card>

      <!-- Browser Compatibility Warning -->
      <q-card v-if="!isSupported" class="q-mt-md bg-warning text-white">
        <q-card-section>
          <div class="text-h6">
            <q-icon name="warning" class="q-mr-sm" />
            Browser Not Supported
          </div>
          <p class="q-mb-none">
            Your browser does not support push notifications.
            Please use Chrome, Firefox, or Edge on desktop, or Chrome on Android.
          </p>
        </q-card-section>
      </q-card>
    </div>
  </q-page>
</template>

<script setup>
import { computed, ref } from 'vue'
import { copyToClipboard, Notify } from 'quasar'
import { usePushNotification } from '../composables/usePushNotification'

const {
  isSubscribed,
  permission,
  loading,
  subscribe,
  unsubscribe,
  sendTestNotification
} = usePushNotification()

const testTitle = ref('Test Notification')
const testBody = ref('This is a test notification from GitHub Star Notifier')

const isSupported = computed(() => {
  return 'Notification' in window && 'serviceWorker' in navigator
})

const subscriptionStatus = computed(() => {
  if (isSubscribed.value) {
    return { color: 'positive', label: 'Subscribed' }
  } else if (permission.value === 'denied') {
    return { color: 'negative', label: 'Permission Denied' }
  } else {
    return { color: 'grey-6', label: 'Not Subscribed' }
  }
})

const webhookUrl = computed(() => {
  return `${window.location.origin}/api/webhook`
})

async function handleSubscribe() {
  try {
    await subscribe()
  } catch (err) {
    console.error('Subscribe failed:', err)
  }
}

async function handleUnsubscribe() {
  try {
    await unsubscribe()
  } catch (err) {
    console.error('Unsubscribe failed:', err)
  }
}

async function handleSendTest() {
  try {
    await sendTestNotification(testTitle.value, testBody.value)
  } catch (err) {
    console.error('Send test failed:', err)
  }
}

function copyWebhookUrl() {
  copyToClipboard(webhookUrl.value)
    .then(() => {
      Notify.create({
        type: 'positive',
        message: 'Webhook URL copied to clipboard',
        position: 'top',
        timeout: 1500
      })
    })
    .catch(() => {
      Notify.create({
        type: 'negative',
        message: 'Failed to copy webhook URL',
        position: 'top'
      })
    })
}
</script>

<style scoped>
.container {
  min-width: 300px;
}

code {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
}
</style>
