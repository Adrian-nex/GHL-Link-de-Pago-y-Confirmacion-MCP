# 🎨 DIAGRAMAS VISUALES - Sistema de Webhooks

## 📊 Flujo Completo del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                    USUARIO REALIZA UN PAGO                          │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         MERCADOPAGO                                 │
│  • Procesa el pago                                                  │
│  • Estado: approved / pending / rejected                            │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               │ POST /webhooks/mp
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              ENDPOINT: /webhooks/mp (tu servidor)                   │
│                                                                     │
│  1. Recibir payload                          [~10ms]               │
│  2. Generar webhook_id único                 [~5ms]                │
│  3. Verificar si ya existe (idempotencia)    [~20ms]               │
│  4. Guardar en tabla webhook_events          [~50ms]               │
│  5. ✅ Responder 200 OK                       [~5ms]                │
│                                                                     │
│  Total: ~90ms ⚡                                                     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               │ Procesamiento asíncrono
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│          WEBHOOK PROCESSOR (background)                             │
│                                                                     │
│  1. Marcar como "processing"                 [~10ms]               │
│  2. Consultar API de MercadoPago             [~2s]                 │
│  3. Actualizar pago en BD                    [~100ms]              │
│  4. Si approved → agregar tag en GHL         [~1s]                 │
│  5. Marcar como "success"                    [~10ms]               │
│                                                                     │
│  Total: ~3.1s (pero no bloquea el webhook) 🚀                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │   ✅ COMPLETADO  │
                      └─────────────────┘
```

---

## 🔄 Flujo de Estados

```
                    ┌──────────────────────────────────────┐
                    │  WEBHOOK RECIBIDO                    │
                    │  webhook_id: payment_123456          │
                    └────────────┬─────────────────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────────────────┐
                    │  STATUS: PENDING                     │
                    │  attempts: 0                         │
                    │  processed: False                    │
                    │  next_retry_at: NULL                 │
                    └────────────┬─────────────────────────┘
                                 │
                                 │ Worker inicia procesamiento
                                 ▼
                    ┌──────────────────────────────────────┐
                    │  STATUS: PROCESSING                  │
                    │  attempts: 1                         │
                    │  processed: False                    │
                    └────────────┬─────────────────────────┘
                                 │
                 ┌───────────────┴────────────────┐
                 │                                │
          ✅ ÉXITO                         ❌ ERROR
                 │                                │
                 ▼                                ▼
    ┌───────────────────────┐      ┌─────────────────────────────┐
    │  STATUS: SUCCESS      │      │  STATUS: PENDING            │
    │  attempts: 1          │      │  attempts: 1                │
    │  processed: True      │      │  next_retry_at: now() + 1m  │
    │  processed_at: now()  │      └────────────┬────────────────┘
    └───────────────────────┘                   │
                                                │ Esperar 1 minuto
                                                ▼
                                   ┌─────────────────────────────┐
                                   │  STATUS: PROCESSING         │
                                   │  attempts: 2                │
                                   └────────────┬────────────────┘
                                                │
                                    ┌───────────┴────────────┐
                                    │                        │
                             ✅ ÉXITO                  ❌ ERROR
                                    │                        │
                                    ▼                        ▼
                       ┌─────────────────┐    ┌──────────────────────────┐
                       │  SUCCESS        │    │  STATUS: PENDING         │
                       └─────────────────┘    │  attempts: 2             │
                                              │  next_retry_at: now()+5m │
                                              └────────────┬─────────────┘
                                                           │
                                                           │ Esperar 5 minutos
                                                           ▼
                                              ┌──────────────────────────┐
                                              │  STATUS: PROCESSING      │
                                              │  attempts: 3             │
                                              └────────────┬─────────────┘
                                                           │
                                               ┌───────────┴────────────┐
                                               │                        │
                                        ✅ ÉXITO                  ❌ ERROR
                                               │                        │
                                               ▼                        ▼
                                  ┌─────────────────┐    ┌──────────────────────┐
                                  │  SUCCESS        │    │  STATUS: FAILED      │
                                  └─────────────────┘    │  attempts: 3         │
                                                         │  processed: False    │
                                                         │  next_retry_at: NULL │
                                                         └──────────────────────┘
```

---

## 🏗️ Arquitectura del Sistema

```
┌───────────────────────────────────────────────────────────────────────┐
│                          CAPA DE PRESENTACIÓN                         │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────┐    ┌──────────────────┐    ┌────────────────┐ │
│  │  Admin Django    │    │  API REST        │    │  Frontend      │ │
│  │  /admin/...      │    │  /api/...        │    │  index.html    │ │
│  └──────────────────┘    └──────────────────┘    └────────────────┘ │
│                                                                       │
└──────────────────────────────────┬────────────────────────────────────┘
                                   │
┌──────────────────────────────────┴────────────────────────────────────┐
│                           CAPA DE LÓGICA                              │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  VIEWS (views.py)                                               │ │
│  │  • mp_webhook()           ← Recibir webhooks                    │ │
│  │  • create_payment()       ← Crear pagos                         │ │
│  │  • get_webhook_events()   ← API historial                       │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  SERVICES (services/)                                           │ │
│  │  • WebhookProcessor       ← Procesar eventos                    │ │
│  │  • process_pending_webhooks() ← Reintentar pendientes           │ │
│  │  • add_tag_to_contact()   ← GHL integración                     │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  COMMANDS (management/commands/)                                │ │
│  │  • process_webhooks       ← Worker manual/automático            │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└──────────────────────────────────┬────────────────────────────────────┘
                                   │
┌──────────────────────────────────┴────────────────────────────────────┐
│                          CAPA DE DATOS                                │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  MODELS (models.py)                                             │ │
│  │  • Payment                ← Pagos                               │ │
│  │  • WebhookEvent           ← Eventos de webhooks                 │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  DATABASE (db.sqlite3)                                          │ │
│  │  • payments_payment                                             │ │
│  │  • payments_webhookevent  ← Nueva tabla                         │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 🔗 Integraciones Externas

```
┌─────────────────────────────────────────────────────────────────┐
│                     TU APLICACIÓN DJANGO                        │
│                                                                 │
│  ┌──────────────┐         ┌─────────────────┐                  │
│  │  /webhooks/mp│         │ WebhookProcessor│                  │
│  └──────┬───────┘         └────────┬────────┘                  │
│         │                          │                            │
└─────────┼──────────────────────────┼────────────────────────────┘
          │                          │
          │                          │
    1. Webhook                 2. Consultar datos
          │                          │
          ▼                          ▼
┌─────────────────────┐    ┌───────────────────────┐
│   MERCADOPAGO       │    │   MERCADOPAGO API     │
│                     │    │                       │
│  • Procesa pagos    │    │  GET /v1/payments/{id}│
│  • Envía webhooks   │    │  GET /merchant_orders │
│                     │    │                       │
└─────────────────────┘    └───────────────────────┘
                                     │
                                     │
                               3. Agregar tag
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │   GOHIGHLEVEL API    │
                          │                      │
                          │  POST /contacts/tag  │
                          │                      │
                          └──────────────────────┘
```

---

## 📈 Timeline de Procesamiento

### Caso Exitoso (sin errores):
```
T+0ms     │ Webhook recibido
          │ ↓ Guardar en BD (~50ms)
T+50ms    │ Responder 200 OK ✅
          │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ MercadoPago recibe confirmación
T+51ms    │ Iniciar procesamiento async
          │ ↓ mark_processing()
T+60ms    │ Consultar API MercadoPago
          │ ↓ (~2 segundos)
T+2060ms  │ Actualizar pago en BD
          │ ↓ (~100ms)
T+2160ms  │ Agregar tag en GHL
          │ ↓ (~1 segundo)
T+3160ms  │ mark_success() ✅
          │
Resultado: COMPLETADO en ~3.2 segundos (pero respuesta en 50ms)
```

### Caso con Reintentos:
```
T+0ms     │ Webhook recibido
T+50ms    │ Responder 200 OK ✅
T+51ms    │ Intento 1: ERROR (API de MP timeout)
          │ ↓ next_retry_at = T + 1min
          │
T+1min    │ process_webhooks ejecuta
T+1min    │ Intento 2: ÉXITO ✅
          │
Resultado: COMPLETADO en 1 minuto (webhook guardado desde T+50ms)
```

---

## 🎯 Componentes Clave

```
╔═══════════════════════════════════════════════════════════════╗
║                  COMPONENTE: WebhookEvent                     ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  Campos principales:                                          ║
║  ┌─────────────────────────────────────────────────────────┐ ║
║  │ webhook_id         VARCHAR(255) UNIQUE                  │ ║
║  │ webhook_type       VARCHAR(50)                          │ ║
║  │ mp_payment_id      VARCHAR(100)                         │ ║
║  │ preference_id      VARCHAR(100)                         │ ║
║  │ payment            ForeignKey(Payment)                  │ ║
║  │ raw_payload        JSON                                 │ ║
║  │ status             VARCHAR(20) [pending/processing/...] │ ║
║  │ processed          BOOLEAN                              │ ║
║  │ attempts           INTEGER                              │ ║
║  │ max_attempts       INTEGER (default: 3)                 │ ║
║  │ last_error         TEXT                                 │ ║
║  │ error_details      JSON                                 │ ║
║  │ created_at         DATETIME                             │ ║
║  │ processed_at       DATETIME                             │ ║
║  │ next_retry_at      DATETIME                             │ ║
║  └─────────────────────────────────────────────────────────┘ ║
║                                                               ║
║  Métodos principales:                                         ║
║  • mark_processing()     ← Iniciar procesamiento             ║
║  • mark_success()        ← Marcar como exitoso               ║
║  • mark_failed(error)    ← Manejar error y programar retry   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

╔═══════════════════════════════════════════════════════════════╗
║               COMPONENTE: WebhookProcessor                    ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  Responsabilidades:                                           ║
║  ┌─────────────────────────────────────────────────────────┐ ║
║  │ 1. Validar tipo de webhook                              │ ║
║  │ 2. Consultar API de MercadoPago                         │ ║
║  │ 3. Parsear respuesta                                    │ ║
║  │ 4. Actualizar modelo Payment                            │ ║
║  │ 5. Integrar con GoHighLevel (si approved)               │ ║
║  │ 6. Manejar errores con reintentos                       │ ║
║  │ 7. Actualizar estado del WebhookEvent                   │ ║
║  └─────────────────────────────────────────────────────────┘ ║
║                                                               ║
║  Flujo de procesamiento:                                      ║
║  process() → _process_payment_webhook()                      ║
║           → _process_merchant_order_webhook()                ║
║           → _add_ghl_tag()                                   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

╔═══════════════════════════════════════════════════════════════╗
║            COMPONENTE: process_webhooks (comando)             ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  Función: Worker para procesar webhooks pendientes            ║
║                                                               ║
║  Algoritmo:                                                   ║
║  ┌─────────────────────────────────────────────────────────┐ ║
║  │ 1. Buscar eventos con:                                  │ ║
║  │    • status = 'pending'                                 │ ║
║  │    • processed = False                                  │ ║
║  │    • next_retry_at <= NOW() OR NULL                     │ ║
║  │                                                         │ ║
║  │ 2. Limitar a 10 eventos por ejecución                  │ ║
║  │                                                         │ ║
║  │ 3. Para cada evento:                                   │ ║
║  │    processor = WebhookProcessor(event)                 │ ║
║  │    processor.process()                                 │ ║
║  │                                                         │ ║
║  │ 4. Loguear resultados                                  │ ║
║  └─────────────────────────────────────────────────────────┘ ║
║                                                               ║
║  Modos de ejecución:                                          ║
║  • python manage.py process_webhooks       (una vez)         ║
║  • python manage.py process_webhooks --loop (continuo)       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## 📊 Tabla de Decisiones

### ¿Cuándo reintentar?

| Condición | Acción | Razón |
|-----------|--------|-------|
| attempts < max_attempts | ✅ Reintentar | Aún hay intentos disponibles |
| attempts >= max_attempts | ❌ Marcar como failed | Ya se agotaron los intentos |
| status = "success" | ⏭️ Ignorar | Ya fue procesado |
| status = "processing" | ⏸️ Esperar | Otro worker lo está procesando |
| next_retry_at > NOW() | ⏰ Esperar | Aún no es momento de reintentar |

### Tiempos de reintento:

| Intento | Delay | Momento | Razón |
|---------|-------|---------|-------|
| 1 | Inmediato | Al recibir | Probar procesamiento directo |
| 2 | +1 minuto | T+1min | Error temporal (timeout, etc) |
| 3 | +5 minutos | T+6min | Problema persistente |
| 4 | +15 minutos | T+21min | Problema serio (última oportunidad) |
| 5+ | ∞ (failed) | - | Fallo permanente |

---

## 🎨 Estados Visuales en el Admin

```
┌─────────────────────────────────────────────────────────┐
│  Estado     │  Color       │  Badge                     │
├─────────────┼──────────────┼────────────────────────────┤
│  pending    │  🟡 Amarillo │  [ PENDIENTE ]             │
│  processing │  🔵 Azul     │  [ PROCESANDO ]            │
│  success    │  🟢 Verde    │  [ EXITOSO ]               │
│  failed     │  🔴 Rojo     │  [ FALLIDO ]               │
└─────────────┴──────────────┴────────────────────────────┘
```

---

Estos diagramas te ayudan a visualizar todo el sistema. 🎯
