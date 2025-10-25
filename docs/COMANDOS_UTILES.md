# 🛠️ COMANDOS ÚTILES - Sistema de Webhooks

## 🚀 Comandos Principales

### Desarrollo

```bash
# Iniciar servidor Django
python manage.py runserver

# Procesar webhooks pendientes (una vez)
python manage.py process_webhooks

# Procesar webhooks continuamente (cada 60 segundos)
python manage.py process_webhooks --loop

# Ver ayuda del comando
python manage.py process_webhooks --help

# Ejecutar tests del sistema
python test_webhooks.py

# Limpiar datos de prueba
python test_webhooks.py --clean
```

### Base de Datos

```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Ver estado de migraciones
python manage.py showmigrations

# Revertir última migración
python manage.py migrate payments 0002

# Shell interactivo de Django
python manage.py shell
```

### Administración

```bash
# Crear superusuario (para admin)
python manage.py createsuperuser

# Recolectar archivos estáticos
python manage.py collectstatic

# Verificar errores del proyecto
python manage.py check
```

---

## 🔍 Consultas Útiles (Django Shell)

### Abrir shell:
```bash
python manage.py shell
```

### Ver estadísticas de webhooks:
```python
from payments.models import WebhookEvent

# Total de eventos
total = WebhookEvent.objects.count()
print(f"Total: {total}")

# Por estado
pending = WebhookEvent.objects.filter(status='pending').count()
success = WebhookEvent.objects.filter(status='success').count()
failed = WebhookEvent.objects.filter(status='failed').count()

print(f"Pendientes: {pending}")
print(f"Exitosos: {success}")
print(f"Fallidos: {failed}")
```

### Ver últimos webhooks:
```python
from payments.models import WebhookEvent

# Últimos 10 eventos
events = WebhookEvent.objects.all().order_by('-created_at')[:10]

for event in events:
    print(f"{event.webhook_id}: {event.status} ({event.attempts} intentos)")
```

### Ver webhooks pendientes:
```python
from payments.models import WebhookEvent
from django.utils import timezone

# Pendientes que deben procesarse ahora
now = timezone.now()
pending = WebhookEvent.objects.filter(
    status='pending',
    processed=False
).filter(
    models.Q(next_retry_at__isnull=True) | models.Q(next_retry_at__lte=now)
)

print(f"Webhooks pendientes: {pending.count()}")

for event in pending:
    print(f"  - {event.webhook_id} (intento {event.attempts}/{event.max_attempts})")
```

### Ver webhooks fallidos:
```python
from payments.models import WebhookEvent

failed = WebhookEvent.objects.filter(status='failed')

print(f"Webhooks fallidos: {failed.count()}")

for event in failed:
    print(f"  - {event.webhook_id}")
    print(f"    Error: {event.last_error}")
    print(f"    Intentos: {event.attempts}")
    print()
```

### Reintentar webhook específico:
```python
from payments.models import WebhookEvent
from django.utils import timezone

# Por ID
event = WebhookEvent.objects.get(id=1)

# Por webhook_id
event = WebhookEvent.objects.get(webhook_id='payment_123456')

# Reintentar
event.status = 'pending'
event.next_retry_at = timezone.now()
event.save()

print(f"Evento {event.webhook_id} programado para reintento")
```

### Reintentar todos los fallidos:
```python
from payments.models import WebhookEvent
from django.utils import timezone

# Obtener todos los fallidos
failed = WebhookEvent.objects.filter(status='failed')

count = 0
for event in failed:
    event.status = 'pending'
    event.next_retry_at = timezone.now()
    event.save()
    count += 1

print(f"{count} eventos programados para reintento")
```

### Ver pagos sin webhook asociado:
```python
from payments.models import Payment, WebhookEvent

# Pagos sin webhooks
payments_without_webhooks = Payment.objects.filter(webhook_events__isnull=True)

print(f"Pagos sin webhooks: {payments_without_webhooks.count()}")

for payment in payments_without_webhooks:
    print(f"  - {payment.appointment_id}: {payment.status}")
```

### Procesar webhook manualmente:
```python
from payments.models import WebhookEvent
from payments.services.webhook_processor import WebhookProcessor

# Obtener evento
event = WebhookEvent.objects.get(webhook_id='payment_123456')

# Procesarlo
processor = WebhookProcessor(event)
result = processor.process()

print(f"Resultado: {'✓ Éxito' if result else '✗ Fallo'}")
print(f"Estado: {event.status}")
print(f"Intentos: {event.attempts}")
```

### Limpiar webhooks de prueba:
```python
from payments.models import WebhookEvent

# Eliminar webhooks de prueba
WebhookEvent.objects.filter(webhook_id__startswith='test_').delete()

print("Webhooks de prueba eliminados")
```

---

## 📊 Consultas SQL Directas

### SQLite (db.sqlite3)

```bash
# Abrir base de datos
sqlite3 db.sqlite3
```

```sql
-- Ver tabla de webhooks
SELECT * FROM payments_webhookevent 
ORDER BY created_at DESC 
LIMIT 10;

-- Estadísticas por estado
SELECT status, COUNT(*) as count
FROM payments_webhookevent
GROUP BY status;

-- Webhooks fallidos con errores
SELECT webhook_id, attempts, last_error
FROM payments_webhookevent
WHERE status = 'failed';

-- Webhooks pendientes que deben procesarse
SELECT webhook_id, attempts, next_retry_at
FROM payments_webhookevent
WHERE status = 'pending'
  AND processed = 0
  AND (next_retry_at IS NULL OR next_retry_at <= datetime('now'));

-- Promedio de intentos por webhook
SELECT AVG(attempts) as avg_attempts
FROM payments_webhookevent
WHERE status = 'success';

-- Tasa de éxito
SELECT 
  (SELECT COUNT(*) FROM payments_webhookevent WHERE status = 'success') * 100.0 / COUNT(*) as success_rate
FROM payments_webhookevent;

-- Webhooks por tipo
SELECT webhook_type, COUNT(*) as count
FROM payments_webhookevent
GROUP BY webhook_type;

-- Tiempo promedio de procesamiento (solo exitosos)
SELECT AVG(
  (julianday(processed_at) - julianday(created_at)) * 24 * 60
) as avg_minutes
FROM payments_webhookevent
WHERE status = 'success' AND processed_at IS NOT NULL;

-- Salir
.quit
```

---

## 🔎 Debugging

### Ver logs en tiempo real:

**PowerShell:**
```powershell
# Ver últimas 50 líneas
Get-Content -Path logs\webhook.log -Tail 50

# Seguir logs en tiempo real
Get-Content -Path logs\webhook.log -Wait -Tail 50
```

**Git Bash / Linux:**
```bash
# Ver últimas 50 líneas
tail -n 50 logs/webhook.log

# Seguir logs en tiempo real
tail -f logs/webhook.log
```

### Filtrar logs:

**PowerShell:**
```powershell
# Solo errores
Get-Content logs\webhook.log | Select-String "ERROR"

# Solo eventos exitosos
Get-Content logs\webhook.log | Select-String "procesado exitosamente"

# Webhook específico
Get-Content logs\webhook.log | Select-String "payment_123456"
```

**Git Bash:**
```bash
# Solo errores
grep ERROR logs/webhook.log

# Solo eventos exitosos
grep "procesado exitosamente" logs/webhook.log

# Webhook específico
grep "payment_123456" logs/webhook.log
```

### Ver errores del servidor:

```bash
# Ver errores de Django
python manage.py check --deploy

# Ver migraciones pendientes
python manage.py showmigrations | findstr "[ ]"
```

---

## 🧪 Testing

### Ejecutar tests:
```bash
# Todos los tests
python test_webhooks.py

# Ver output detallado
python test_webhooks.py 2>&1

# Guardar output en archivo
python test_webhooks.py > test_results.txt 2>&1
```

### Crear webhook de prueba:
```bash
python manage.py shell
```

```python
from payments.models import WebhookEvent, Payment

# Crear pago de prueba
payment = Payment.objects.create(
    appointment_id='TEST_001',
    contact_id='test_contact',
    preference_id='test_pref',
    amount=100.00,
    status='pending'
)

# Crear webhook de prueba
event = WebhookEvent.objects.create(
    webhook_id='test_payment_123',
    webhook_type='payment',
    mp_payment_id='123',
    preference_id=payment.preference_id,
    payment=payment,
    raw_payload={'test': 'data'},
    status='pending'
)

print(f"Webhook de prueba creado: {event.id}")
```

### Simular procesamiento:
```python
from payments.services.webhook_processor import WebhookProcessor

processor = WebhookProcessor(event)
result = processor.process()

print(f"Resultado: {result}")
print(f"Estado: {event.status}")
```

---

## 📡 Probar API

### Con curl (Git Bash):

```bash
# Ver historial de webhooks
curl http://localhost:8000/api/webhook-events

# Filtrar por estado
curl http://localhost:8000/api/webhook-events?status=pending

# Filtrar por tipo
curl http://localhost:8000/api/webhook-events?type=payment

# Limitar resultados
curl http://localhost:8000/api/webhook-events?limit=5

# Ver pagos
curl http://localhost:8000/api/payments

# Ver contactos
curl http://localhost:8000/api/contacts
```

### Con PowerShell:

```powershell
# Ver historial de webhooks
Invoke-RestMethod -Uri "http://localhost:8000/api/webhook-events"

# Filtrar por estado
Invoke-RestMethod -Uri "http://localhost:8000/api/webhook-events?status=pending"

# Ver respuesta formateada
Invoke-RestMethod -Uri "http://localhost:8000/api/webhook-events" | ConvertTo-Json -Depth 10
```

### Con navegador:
```
http://localhost:8000/api/webhook-events
http://localhost:8000/api/webhook-events?status=pending
http://localhost:8000/api/webhook-events?type=payment
http://localhost:8000/api/payments
```

---

## 🔄 Automatización

### Windows Task Scheduler (PowerShell):

```powershell
# Ver tareas existentes
Get-ScheduledTask | Where-Object {$_.TaskName -like "*webhook*"}

# Ejecutar tarea manualmente
Start-ScheduledTask -TaskName "Procesar Webhooks Django"

# Ver última ejecución
Get-ScheduledTaskInfo -TaskName "Procesar Webhooks Django"

# Deshabilitar tarea
Disable-ScheduledTask -TaskName "Procesar Webhooks Django"

# Habilitar tarea
Enable-ScheduledTask -TaskName "Procesar Webhooks Django"
```

### Crear tarea desde PowerShell:

```powershell
# Variables
$pythonPath = "C:\Python313\python.exe"
$projectPath = "C:\Users\Ignacio\Downloads\ghl-payments"
$scriptPath = "$projectPath\manage.py"

# Crear acción
$action = New-ScheduledTaskAction -Execute $pythonPath `
    -Argument "manage.py process_webhooks" `
    -WorkingDirectory $projectPath

# Crear trigger (cada 1 minuto)
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 1)

# Crear configuración
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

# Registrar tarea
Register-ScheduledTask -TaskName "Procesar Webhooks Django" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Procesa webhooks pendientes de MercadoPago"
```

---

## 🛡️ Mantenimiento

### Limpiar webhooks antiguos (exitosos):

```bash
python manage.py shell
```

```python
from payments.models import WebhookEvent
from django.utils import timezone
from datetime import timedelta

# Eliminar webhooks exitosos de hace más de 30 días
cutoff_date = timezone.now() - timedelta(days=30)

old_events = WebhookEvent.objects.filter(
    status='success',
    processed_at__lt=cutoff_date
)

count = old_events.count()
old_events.delete()

print(f"Eliminados {count} webhooks antiguos")
```

### Backup de base de datos:

```powershell
# Crear backup
Copy-Item db.sqlite3 "db_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').sqlite3"

# Ver backups
Get-ChildItem -Filter "db_backup_*.sqlite3" | Sort-Object LastWriteTime -Descending
```

### Limpiar logs antiguos:

```powershell
# Crear backup de logs
Copy-Item logs\webhook.log "logs\webhook_$(Get-Date -Format 'yyyyMMdd').log"

# Limpiar log actual
Clear-Content logs\webhook.log
```

---

## 📈 Monitoreo

### Ver estadísticas rápidas:

```bash
python manage.py shell
```

```python
from payments.models import WebhookEvent, Payment

# Resumen general
print("=== ESTADÍSTICAS ===")
print(f"Total webhooks: {WebhookEvent.objects.count()}")
print(f"Total pagos: {Payment.objects.count()}")
print()

# Por estado
print("=== WEBHOOKS POR ESTADO ===")
for status, label in WebhookEvent.STATUS_CHOICES:
    count = WebhookEvent.objects.filter(status=status).count()
    print(f"{label}: {count}")
print()

# Pagos por estado
print("=== PAGOS POR ESTADO ===")
from django.db.models import Count
payment_stats = Payment.objects.values('status').annotate(count=Count('id'))
for stat in payment_stats:
    print(f"{stat['status']}: {stat['count']}")
```

### Crear script de monitoreo:

```python
# monitor_webhooks.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from payments.models import WebhookEvent
from django.db.models import Count

def monitor():
    print("\n" + "="*60)
    print("MONITOR DE WEBHOOKS")
    print("="*60)
    
    # Por estado
    stats = WebhookEvent.objects.values('status').annotate(count=Count('id'))
    
    for stat in stats:
        status = stat['status']
        count = stat['count']
        icon = {
            'pending': '⏳',
            'processing': '⚡',
            'success': '✅',
            'failed': '❌'
        }.get(status, '❓')
        
        print(f"{icon} {status.upper()}: {count}")
    
    # Webhooks fallidos recientes
    failed = WebhookEvent.objects.filter(status='failed').order_by('-created_at')[:5]
    
    if failed:
        print("\n⚠️  WEBHOOKS FALLIDOS RECIENTES:")
        for event in failed:
            print(f"  - {event.webhook_id}: {event.last_error[:50]}...")

if __name__ == '__main__':
    monitor()
```

Ejecutar:
```bash
python monitor_webhooks.py
```

---

## 🎯 Atajos Útiles

### Alias de PowerShell:

Agregar al perfil (`$PROFILE`):

```powershell
# Alias para comandos frecuentes
function Start-Django { python manage.py runserver }
function Process-Webhooks { python manage.py process_webhooks }
function Process-Webhooks-Loop { python manage.py process_webhooks --loop }
function Django-Shell { python manage.py shell }
function Watch-Logs { Get-Content -Path logs\webhook.log -Wait -Tail 50 }

Set-Alias dj Start-Django
Set-Alias pw Process-Webhooks
Set-Alias pwl Process-Webhooks-Loop
Set-Alias ds Django-Shell
Set-Alias wl Watch-Logs
```

Usar:
```powershell
dj      # Iniciar servidor
pw      # Procesar webhooks
pwl     # Procesar webhooks (loop)
ds      # Django shell
wl      # Ver logs en tiempo real
```

---

**💡 Guarda este documento como referencia rápida!**
