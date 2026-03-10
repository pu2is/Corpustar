<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  BACKEND_BASE_URL,
  BACKEND_PORT,
  FRONTEND_DEV_PORT,
} from '../config/ports.mjs'

type HealthResponse = {
  status: string
}

type BackendState = 'checking' | 'online' | 'offline'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || BACKEND_BASE_URL
const apiHealthUrl = `${apiBaseUrl}/api/health`

const backendState = ref<BackendState>('checking')
const backendMessage = ref('Checking FastAPI health endpoint...')
const lastCheckedAt = ref('')

const stateLabel = computed(() => {
  switch (backendState.value) {
    case 'online':
      return 'Backend reachable'
    case 'offline':
      return 'Backend unavailable'
    default:
      return 'Checking backend'
  }
})

async function checkBackend() {
  backendState.value = 'checking'
  backendMessage.value = `Calling ${apiHealthUrl}`

  try {
    const response = await fetch(apiHealthUrl)
    if (!response.ok) {
      throw new Error(`Health check returned ${response.status}`)
    }

    const payload = (await response.json()) as HealthResponse
    backendState.value = payload.status === 'ok' ? 'online' : 'offline'
    backendMessage.value = `FastAPI responded with status "${payload.status}".`
  } catch (error) {
    backendState.value = 'offline'
    backendMessage.value =
      error instanceof Error ? error.message : 'Unable to reach the backend.'
  } finally {
    lastCheckedAt.value = new Date().toLocaleTimeString()
  }
}

onMounted(() => {
  void checkBackend()
})
</script>

<template>
  <main class="app-shell">
    <section class="status-card">
      <p class="eyebrow">Corpustar</p>
      <h1>FastAPI on {{ BACKEND_PORT }}. Vite + Electron on {{ FRONTEND_DEV_PORT }}.</h1>
      <p class="lede">
        The frontend is served on port {{ FRONTEND_DEV_PORT }} and checks the backend health
        endpoint on startup.
      </p>

      <div class="status-row" :data-state="backendState">
        <div class="status-copy">
          <span class="status-dot" />
          <div>
            <strong>{{ stateLabel }}</strong>
            <p>{{ backendMessage }}</p>
            <small v-if="lastCheckedAt">Last checked at {{ lastCheckedAt }}</small>
          </div>
        </div>
        <button type="button" @click="checkBackend">Retry</button>
      </div>

      <div class="endpoint-grid">
        <article>
          <span>Frontend</span>
          <strong>http://127.0.0.1:{{ FRONTEND_DEV_PORT }}</strong>
        </article>
        <article>
          <span>Backend</span>
          <strong>{{ apiBaseUrl }}</strong>
        </article>
        <article>
          <span>Health</span>
          <strong>{{ apiHealthUrl }}</strong>
        </article>
      </div>
    </section>
  </main>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
}

.status-card {
  width: min(760px, 100%);
  padding: 32px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 28px;
  background: rgba(6, 12, 20, 0.78);
  box-shadow: 0 32px 80px rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(18px);
}

.eyebrow {
  margin: 0 0 12px;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #7dd3fc;
}

h1 {
  margin: 0;
  font-size: clamp(2.3rem, 5vw, 4.1rem);
  line-height: 0.95;
}

.lede {
  margin: 18px 0 0;
  max-width: 56ch;
  color: #cbd5e1;
}

.status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 28px;
  padding: 18px 20px;
  border-radius: 20px;
  background: rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(148, 163, 184, 0.16);
}

.status-row[data-state='online'] {
  border-color: rgba(34, 197, 94, 0.45);
}

.status-row[data-state='offline'] {
  border-color: rgba(248, 113, 113, 0.45);
}

.status-copy {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.status-copy p,
.status-copy small {
  display: block;
  margin-top: 4px;
  color: #cbd5e1;
}

.status-dot {
  width: 12px;
  height: 12px;
  margin-top: 6px;
  flex: 0 0 auto;
  border-radius: 999px;
  background: #f59e0b;
  box-shadow: 0 0 0 8px rgba(245, 158, 11, 0.12);
}

.status-row[data-state='online'] .status-dot {
  background: #22c55e;
  box-shadow: 0 0 0 8px rgba(34, 197, 94, 0.12);
}

.status-row[data-state='offline'] .status-dot {
  background: #f87171;
  box-shadow: 0 0 0 8px rgba(248, 113, 113, 0.12);
}

.endpoint-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-top: 24px;
}

.endpoint-grid article {
  padding: 18px;
  border-radius: 18px;
  background: rgba(15, 23, 42, 0.72);
  border: 1px solid rgba(148, 163, 184, 0.14);
}

.endpoint-grid span {
  display: block;
  font-size: 0.85rem;
  color: #94a3b8;
}

.endpoint-grid strong {
  display: block;
  margin-top: 10px;
  overflow-wrap: anywhere;
}

@media (max-width: 720px) {
  .status-card {
    padding: 24px;
  }

  .status-row {
    flex-direction: column;
    align-items: stretch;
  }

  .endpoint-grid {
    grid-template-columns: 1fr;
  }
}
</style>
