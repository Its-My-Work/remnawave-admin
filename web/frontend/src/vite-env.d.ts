/// <reference types="vite/client" />

interface RuntimeEnv {
  API_URL?: string
  WS_URL?: string
  TELEGRAM_BOT_USERNAME?: string
  SECRET_PATH?: string
}

declare global {
  interface Window {
    __ENV?: RuntimeEnv
  }
}
