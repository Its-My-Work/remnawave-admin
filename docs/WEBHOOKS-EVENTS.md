# Webhook Event Catalog

All events share the envelope:

```json
{
  "event": "<event name>",
  "data": { ... }
}
```

This document describes the `data` payload for each event. Payloads may grow over time;
receivers should **ignore unknown fields** (backward-compatible evolution).

---

## `user.created`

Fires when a new user is created via admin UI or API.

```json
{
  "uuid": "e4f...",
  "username": "alice",
  "status": "active",
  "traffic_limit_bytes": 107374182400,
  "expire_at": "2026-06-01T00:00:00Z",
  "tag": "vip",
  "description": "Created via CI",
  "created_at": "2026-04-16T11:23:45Z"
}
```

## `user.updated`

Fires when any mutable field changes (traffic limit, expire, status, description).

```json
{
  "uuid": "e4f...",
  "username": "alice",
  "changes": {
    "traffic_limit_bytes": {"old": 107374182400, "new": 214748364800},
    "status": {"old": "active", "new": "disabled"}
  },
  "updated_at": "2026-04-16T11:25:01Z"
}
```

Only changed fields appear under `changes`.

## `user.deleted`

```json
{
  "uuid": "e4f...",
  "username": "alice",
  "deleted_at": "2026-04-16T11:30:00Z"
}
```

---

## `node.online`

A node has just connected (transitioned from offline -> online).

```json
{
  "uuid": "...",
  "name": "eu-west-1",
  "address": "1.2.3.4",
  "port": 62050,
  "connected_at": "2026-04-16T11:40:22Z"
}
```

## `node.offline`

A node has lost connection.

```json
{
  "uuid": "...",
  "name": "eu-west-1",
  "last_seen_at": "2026-04-16T11:45:05Z",
  "downtime_seconds": 30
}
```

---

## `violation.created`

A new anti-abuse violation has been detected.

```json
{
  "id": 9123,
  "user_uuid": "...",
  "username": "alice",
  "severity": "high",
  "score": 0.82,
  "recommended_action": "temp_block",
  "analyzers": {
    "temporal": 0.9,
    "geo": 0.6,
    "asn": 0.3,
    "profile": 0.7,
    "device": 0.2
  },
  "evidence": {
    "simultaneous_connections": 4,
    "countries": ["RU", "US", "NL"],
    "asn_types": ["datacenter"]
  },
  "detected_at": "2026-04-16T11:50:00Z"
}
```

See `docs/anti-abuse.md` for analyzer internals (if present in the repo).

---

## `backup.created`

A scheduled or manual backup completed successfully.

```json
{
  "id": 203,
  "filename": "backup_2026-04-16T11-55-00.sql.gz",
  "size_bytes": 4_837_293,
  "created_at": "2026-04-16T11:55:00Z",
  "trigger": "schedule"
}
```

`trigger` is `schedule` or `manual`.

---

## `webhook.test`

Sent only when an admin clicks **Send test delivery** in the UI. This event is **not**
persisted to `webhook_deliveries` (tests are ephemeral) and never participates in the
retry queue.

```json
{
  "message": "This is a test payload from Remnawave Admin.",
  "webhook_id": 42
}
```

Use it in dev to verify connectivity, headers, and signature verification.

---

## Scheduled vs real-time

All events above are fired in-band from the code path that mutates the underlying state.
There is no batching - one logical event = one HTTP POST per matching subscription.

## Ordering

Deliveries are not strictly ordered. If order matters for your integration, use the
timestamp fields (`created_at`, `updated_at`, `detected_at`) on the payload itself.

## Idempotency

Events currently do not carry a globally unique `event_id`. Receivers that need dedup should
key off (resource id + timestamp). An `event_id` field is planned for a future release.
