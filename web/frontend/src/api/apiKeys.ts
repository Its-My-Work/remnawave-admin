import client from './client'

export interface ApiKey {
  id: number
  name: string
  key_prefix: string
  scopes: string[]
  is_active: boolean
  expires_at: string | null
  last_used_at: string | null
  created_by_username: string | null
  description: string | null
  created_at: string
}

export interface ApiKeyCreated extends ApiKey {
  raw_key: string
}

export interface WebhookSubscription {
  id: number
  name: string
  url: string
  has_secret: boolean
  events: string[]
  is_active: boolean
  last_triggered_at: string | null
  failure_count: number
  consecutive_failures: number
  auto_disabled_at: string | null
  disabled_reason: string | null
  signature_version: 'v1' | 'v2'
  description: string | null
  created_at: string
}

export interface WebhookDelivery {
  id: number
  webhook_id: number
  event: string
  status_code: number
  response_body: string | null
  error: string | null
  duration_ms: number | null
  sent_at: string
}

export interface WebhookTestResult {
  status_code: number | null
  response_body: string | null
  error: string | null
  duration_ms: number | null
}

export const apiKeysApi = {
  list: async (): Promise<ApiKey[]> => {
    const { data } = await client.get('/api-keys/')
    return Array.isArray(data) ? data : []
  },
  getScopes: async (): Promise<string[]> => {
    const { data } = await client.get('/api-keys/scopes')
    return data?.scopes || []
  },
  create: async (payload: { name: string; scopes: string[]; expires_at?: string; description?: string }): Promise<ApiKeyCreated> => {
    const { data } = await client.post('/api-keys/', payload)
    return data
  },
  update: async (id: number, payload: { name?: string; scopes?: string[]; is_active?: boolean; description?: string }): Promise<ApiKey> => {
    const { data } = await client.patch(`/api-keys/${id}`, payload)
    return data
  },
  rotate: async (id: number): Promise<ApiKeyCreated> => {
    const { data } = await client.post(`/api-keys/${id}/rotate`)
    return data
  },
  delete: async (id: number): Promise<void> => {
    await client.delete(`/api-keys/${id}`)
  },
}

export const webhooksApi = {
  list: async (): Promise<WebhookSubscription[]> => {
    const { data } = await client.get('/webhooks/')
    return Array.isArray(data) ? data : []
  },
  getEvents: async (): Promise<string[]> => {
    const { data } = await client.get('/webhooks/events')
    return data?.events || []
  },
  create: async (payload: { name: string; url: string; secret?: string; events: string[]; signature_version?: 'v1' | 'v2'; description?: string }): Promise<WebhookSubscription> => {
    const { data } = await client.post('/webhooks/', payload)
    return data
  },
  update: async (
    id: number,
    payload: { name?: string; url?: string; secret?: string; events?: string[]; is_active?: boolean; signature_version?: 'v1' | 'v2'; description?: string },
  ): Promise<WebhookSubscription> => {
    const { data } = await client.patch(`/webhooks/${id}`, payload)
    return data
  },
  delete: async (id: number): Promise<void> => {
    await client.delete(`/webhooks/${id}`)
  },
  test: async (id: number): Promise<WebhookTestResult> => {
    const { data } = await client.post(`/webhooks/${id}/test`)
    return data
  },
  deliveries: async (id: number, limit = 50): Promise<WebhookDelivery[]> => {
    const { data } = await client.get(`/webhooks/${id}/deliveries`, { params: { limit } })
    return Array.isArray(data) ? data : []
  },
}
