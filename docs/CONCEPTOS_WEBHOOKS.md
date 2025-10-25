# 🧠 Conceptos del Ejercicio 2 - Reintentos y Colas de Webhooks

## 🎓 Conceptos Explicados

### 1. **Event-Driven Architecture** (Arquitectura basada en eventos)

#### ¿Qué es?
Un patrón donde las acciones se ejecutan en respuesta a eventos, en lugar de forma secuencial y síncrona.

#### En nuestro caso:
```python
# ❌ SÍNCRONO (Malo):
def webhook(request):
    payload = request.body
    # 1. Consultar API (2 segundos)
    # 2. Actualizar BD (1 segundo)
    # 3. Llamar a GHL (2 segundos)
    return Response(200)  # ¡Tardamos 5 segundos!

# ✅ ASÍNCRONO (Bueno):
def webhook(request):
    payload = request.body
    save_event(payload)  # Guardar (100ms)
    return Response(200)  # ¡Respondemos en 100ms!
    # Luego procesamos en background
```

#### Beneficios:
- **Rapidez**: Respondemos inmediatamente (MercadoPago no reintenta)
- **Confiabilidad**: Si falla el procesamiento, el evento está guardado
- **Escalabilidad**: Podemos procesar muchos webhooks en paralelo

---

### 2. **Idempotencia** (Evitar duplicados)

#### ¿Qué es?
Una operación es idempotente si ejecutarla múltiples veces produce el mismo resultado que ejecutarla una vez.

#### En nuestro caso:
```python
# Campo único en la base de datos
webhook_id = models.CharField(max_length=255, unique=True)

# Verificar antes de guardar
if WebhookEvent.objects.filter(webhook_id=webhook_id).exists():
    return {"status": "already_received"}  # Ignorar duplicado
```

#### ¿Por qué es importante?
MercadoPago puede enviar el mismo webhook múltiples veces:
- Si no responde en 22 segundos
- Si hay error de red
- Por política de reintentos

Sin idempotencia, podríamos:
- ❌ Procesar el mismo pago 2 veces
- ❌ Agregar el mismo tag 2 veces en GHL
- ❌ Crear registros duplicados

Con idempotencia:
- ✅ Detectamos el webhook duplicado
- ✅ Lo ignoramos
- ✅ Respondemos 200 OK (para que MP no reintente)

---

### 3. **Retry Policy** (Política de reintentos)

#### ¿Qué es?
Define cómo y cuándo reintentar una operación fallida.

#### Nuestros parámetros:
```python
max_attempts = 3           # Máximo de reintentos
attempts = 0               # Contador actual
next_retry_at = None       # Cuándo reintentar
```

#### Estrategia: Backoff Exponencial
```python
# Tiempos de espera crecientes
retry_delays = [60, 300, 900]  # 1min, 5min, 15min

# Si falla:
delay = retry_delays[attempts - 1]
next_retry_at = now + delay
```

#### ¿Por qué exponencial?
- **Intento 1 → +1min**: Error temporal (ej: timeout)
- **Intento 2 → +5min**: Problema más persistente
- **Intento 3 → +15min**: Problema serio (ej: API caída)

Si esperáramos siempre 1 minuto:
- ❌ Sobrecargamos el servidor con reintentos
- ❌ No damos tiempo para que se resuelva el problema

Con backoff exponencial:
- ✅ Damos tiempo para recuperación
- ✅ Reducimos carga en el servidor
- ✅ Aumentamos probabilidad de éxito

---

### 4. **Colas y Workers** (Separación de recepción y ejecución)

#### ¿Qué es?
Separar quién **recibe** el trabajo de quién lo **ejecuta**.

#### Arquitectura:

```
┌──────────────┐
│   Receptor   │  ← Recibe webhooks (rápido)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│     Cola     │  ← Almacena eventos pendientes (BD)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    Worker    │  ← Procesa eventos (lento)
└──────────────┘
```

#### En nuestro sistema:

**Receptor** (`mp_webhook` endpoint):
```python
def mp_webhook(request):
    # Solo guarda en BD
    event = WebhookEvent.create(...)
    return Response(200)  # ¡Rápido!
```

**Cola** (tabla `webhook_events`):
```sql
-- Eventos esperando procesamiento
SELECT * FROM webhook_events 
WHERE status = 'pending' 
  AND (next_retry_at IS NULL OR next_retry_at <= NOW())
```

**Worker** (comando `process_webhooks`):
```python
def process_webhooks():
    # Busca eventos pendientes
    events = WebhookEvent.filter(status='pending', ...)
    
    # Procesa cada uno
    for event in events:
        WebhookProcessor(event).process()
```

#### Beneficios:
- **Desacoplamiento**: Receptor y procesador son independientes
- **Escalabilidad**: Podemos tener múltiples workers
- **Resilencia**: Si un worker falla, otro puede continuar

---

### 5. **Estados de un Webhook** (State Machine)

#### Flujo de estados:

```
┌─────────┐
│ pending │  ← Estado inicial (recién recibido)
└────┬────┘
     │
     ▼
┌────────────┐
│ processing │  ← En proceso de ejecución
└─────┬──────┘
      │
      ├─ Éxito → ┌─────────┐
      │          │ success │  ← Procesado exitosamente
      │          └─────────┘
      │
      └─ Error → ┌─────────┐
                 │ pending │  ← Volver a pending (para reintento)
                 └────┬────┘
                      │
                      │ (después de 3 intentos)
                      ▼
                 ┌─────────┐
                 │ failed  │  ← Falló permanentemente
                 └─────────┘
```

#### Transiciones:

```python
# Estado inicial
event.status = 'pending'
event.attempts = 0

# Al empezar a procesar
event.mark_processing()
# → status = 'processing'
# → attempts += 1

# Si tiene éxito
event.mark_success()
# → status = 'success'
# → processed = True
# → processed_at = now()

# Si falla
event.mark_failed("Error message")
# → status = 'pending' (si attempts < max_attempts)
# → status = 'failed' (si attempts >= max_attempts)
# → next_retry_at = now() + delay
```

---

### 6. **Observabilidad** (Logging y Monitoreo)

#### ¿Qué es?
Capacidad de entender qué está pasando en el sistema.

#### Niveles de logging:

```python
import logging
logger = logging.getLogger(__name__)

# DEBUG: Información detallada (desarrollo)
logger.debug("Payload recibido: {...}")

# INFO: Eventos importantes (normal)
logger.info("✓ Evento procesado exitosamente")

# WARNING: Algo raro pero no crítico
logger.warning("⚠ Intento 2 falló, reintentando...")

# ERROR: Error que requiere atención
logger.error("✗ API de MercadoPago no responde")
```

#### Nuestro logging:

```python
# Al recibir webhook
logger.info(f"[WEBHOOK] ✓ Evento {webhook_id} guardado en BD")

# Al procesar
logger.info(f"[WEBHOOK-PROCESSOR] Procesando evento {webhook_id} (intento {attempts}/{max_attempts})")

# Éxito
logger.info(f"[WEBHOOK-PROCESSOR] ✓ Evento {webhook_id} procesado exitosamente")

# Fallo temporal
logger.warning(f"[WEBHOOK-PROCESSOR] ⚠ Evento {webhook_id} falló. Reintento en {delay}s")

# Fallo permanente
logger.error(f"[WEBHOOK-PROCESSOR] ✗ Evento {webhook_id} falló permanentemente: {error}")
```

#### Beneficios:
- **Debugging**: Ver qué pasó en cada momento
- **Auditoría**: Historial completo de eventos
- **Alertas**: Detectar problemas rápidamente
- **Análisis**: Identificar patrones de errores

---

### 7. **Concurrencia** (Evitar procesamiento simultáneo)

#### Problema:
Si dos workers intentan procesar el mismo evento simultáneamente:

```
Worker 1: Lee evento (status=pending)
Worker 2: Lee evento (status=pending)
Worker 1: Procesa evento
Worker 2: Procesa evento  ← ¡Duplicado!
```

#### Solución: Estado "processing"

```python
# Worker 1
event = WebhookEvent.get(id=1)
event.mark_processing()  # status='processing'
# Ahora Worker 2 no lo procesará
```

```python
# Worker 2
events = WebhookEvent.filter(status='pending')
# No incluye el evento en 'processing'
```

#### Implementación:

```python
# Buscar solo eventos pendientes (no en processing)
pending_events = WebhookEvent.objects.filter(
    status=WebhookEvent.STATUS_PENDING,  # No 'processing'
    processed=False
)
```

---

## 🎯 Aplicación Real

### Escenario 1: Usuario realiza un pago

```
1. Usuario paga con MercadoPago
2. MP envía webhook → /webhooks/mp
3. Guardamos evento (ID: payment_123456)
4. Respondemos 200 OK en 100ms
5. Procesamos en background:
   - Consultamos API de MP (2s)
   - Actualizamos pago en BD (100ms)
   - Agregamos tag en GHL (1s)
6. Estado final: success ✓
```

### Escenario 2: API de MercadoPago temporalmente caída

```
1. Usuario paga con MercadoPago
2. MP envía webhook → /webhooks/mp
3. Guardamos evento (ID: payment_789012)
4. Respondemos 200 OK en 100ms
5. Intento 1 de procesamiento:
   - Error: API de MP timeout
   - next_retry_at = now + 1min
6. Después de 1 minuto:
   - Intento 2: ✓ Éxito
   - Estado: success
```

### Escenario 3: Webhook duplicado

```
1. MP envía webhook (payment_111222)
2. Guardamos evento
3. Respondemos 200 OK
4. MP no recibe respuesta (problema de red)
5. MP reenvía webhook (payment_111222)
6. Detectamos: webhook_id ya existe
7. Respondemos: {"status": "already_received"}
8. No procesamos de nuevo ✓
```

---

## 💡 Preguntas Frecuentes

### ¿Por qué no procesar directamente en el endpoint?

**Problema:**
```python
def webhook(request):
    process_payment()  # Tarda 5 segundos
    return Response(200)  # Muy lento!
```

Si tardamos más de 22 segundos, MercadoPago:
- ❌ Marca el webhook como fallido
- ❌ Lo reintenta múltiples veces
- ❌ Podemos procesar duplicados

**Solución:**
```python
def webhook(request):
    save_event()  # 100ms
    return Response(200)  # ¡Rápido!
    # Procesamos después en background
```

### ¿Cuándo usar Celery vs nuestro sistema?

**Nuestro sistema (simple):**
- ✅ Fácil de implementar
- ✅ No requiere dependencias extra
- ✅ Suficiente para volumen bajo-medio
- ❌ Un solo worker (comando manual)
- ❌ No es distribuido

**Celery (avanzado):**
- ✅ Múltiples workers en paralelo
- ✅ Distribuido (varios servidores)
- ✅ Prioridades de tareas
- ✅ Monitoreo avanzado (Flower)
- ❌ Más complejo
- ❌ Requiere Redis/RabbitMQ

**Recomendación:**
- Empieza con nuestro sistema simple
- Si necesitas > 100 webhooks/minuto → migra a Celery

### ¿Qué pasa si el servidor Django se cae?

**Con nuestro sistema:**
1. Webhooks se pierden mientras esté caído
2. Al reiniciar, los webhooks pendientes se procesan
3. Los que llegaron mientras estaba caído se pierden (pero MP los reintenta)

**Mitigación:**
- Usar supervisor/systemd para reinicio automático
- Configurar Task Scheduler para ejecutar `process_webhooks` periódicamente
- Monitoreo de uptime (ej: UptimeRobot)

---

## 🚀 Evolución del Sistema

### Fase 1: Sin reintentos (tu sistema anterior)
```python
def webhook(request):
    process_payment()
    return Response(200)
```
- ❌ Si falla, se pierde
- ❌ Si es lento, MP reintenta

### Fase 2: Guardar primero (implementado ahora)
```python
def webhook(request):
    save_event()
    return Response(200)
    process_in_background()
```
- ✅ Nunca se pierde
- ✅ Respuesta rápida
- ✅ Reintentos automáticos

### Fase 3: Con Celery (futuro)
```python
def webhook(request):
    save_event()
    process_webhook.delay(event_id)  # Celery task
    return Response(200)
```
- ✅ Todo lo anterior +
- ✅ Procesamiento distribuido
- ✅ Múltiples workers
- ✅ Prioridades

---

## 📚 Recursos Adicionales

### Lecturas recomendadas:
- [Webhook Best Practices](https://webhooks.fyi/)
- [Event-Driven Architecture](https://martinfowler.com/articles/201701-event-driven.html)
- [Idempotency Keys](https://brandur.org/idempotency-keys)

### Django:
- [Django Custom Commands](https://docs.djangoproject.com/en/5.0/howto/custom-management-commands/)
- [Django Query Optimization](https://docs.djangoproject.com/en/5.0/topics/db/optimization/)

### Celery (para el futuro):
- [Celery Documentation](https://docs.celeryproject.org/)
- [Django + Celery Tutorial](https://realpython.com/asynchronous-tasks-with-django-and-celery/)

---

**🎉 ¡Felicidades! Ahora entiendes los conceptos clave de sistemas de webhooks production-ready.**
