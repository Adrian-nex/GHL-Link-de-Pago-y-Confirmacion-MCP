# Integración MercadoPago + GoHighLevel - ReflexoPerú

## 📋 Día 3: Actualizar en GHL + Demo

Este proyecto integra MercadoPago con GoHighLevel para agregar automáticamente un tag `pago_confirmado` a los contactos cuando se confirma un pago.

## 🚀 Características Implementadas

- ✅ Creación de preferencias de pago en MercadoPago
- ✅ Webhook para recibir notificaciones de pago
- ✅ Actualización automática en GoHighLevel cuando un pago es aprobado
- ✅ Sistema de tags: se agrega `pago_confirmado` al contacto
- ✅ Logging detallado para seguimiento
- ✅ Prevención de webhooks duplicados

## 🔧 Configuración

### Variables de Entorno (.env)

```env
# MercadoPago
MP_ACCESS_TOKEN=APP_USR-xxxxx
MP_PUBLIC_KEY=APP_USR-xxxxx

# Base URL (ngrok o producción)
BASE_URL=https://tu-dominio.ngrok-free.app

# GoHighLevel
GHL_TOKEN=pit-xxxxx
GHL_BASE_URL=https://services.leadconnectorhq.com/
```

### Instalación

```bash
# 1. Instalar dependencias
pip install django requests python-dotenv

# 2. Ejecutar migraciones
python manage.py migrate

# 3. Iniciar servidor
python manage.py runserver
```

## 📡 Flujo de Integración

### 1. Crear Preferencia de Pago

**Endpoint:** `POST /payments/create`

**Request:**
```json
{
  "appointmentId": "apt_12345",
  "contactId": "ghl_contact_id_123",
  "amount": 100.00,
  "description": "Consulta Fisioterapia"
}
```

**Response:**
```json
{
  "success": true,
  "init_point": "https://www.mercadopago.com.pe/checkout/v1/redirect?pref_id=xxxxx",
  "preference_id": "xxxxx-xxxxx-xxxxx",
  "payment_id": null,
  "status": "pending"
}
```

### 2. Cliente Realiza el Pago

El cliente es redirigido a `init_point` y completa el pago en el sandbox de MercadoPago.

**Credenciales de prueba (Sandbox):**
- Tarjeta: `5031 7557 3453 0604`
- Vencimiento: cualquier fecha futura
- CVV: cualquier 3 dígitos
- Nombre: `APRO` (para aprobar) o `OTHE` (para rechazar)

### 3. Webhook de MercadoPago

MercadoPago envía notificación al webhook:

**Endpoint:** `POST /webhooks/mp`

El webhook:
1. ✅ Verifica que el pago existe en la BD
2. ✅ Actualiza el estado del pago a `approved`
3. ✅ **Llama a GHL para agregar el tag `pago_confirmado`**
4. ✅ Registra todo en logs

### 4. Actualización en GoHighLevel

Cuando el pago es aprobado (`status="approved"`), el sistema automáticamente:

1. Obtiene el `contact_id` del registro de pago
2. Llama a la API de GHL para agregar el tag `pago_confirmado`
3. Verifica que el tag no exista previamente
4. Agrega el tag a la lista de tags del contacto

**Logs esperados:**
```
[PAYMENT] ID: 123456789 | Status: approved | Amount: $100.0 | Payer: test@email.com
[PAYMENT] Saved: 123456789 -> approved
[GHL] Intentando agregar tag a contacto ghl_contact_id_123
[GHL] ✓ Tag agregado exitosamente: Tag 'pago_confirmado' agregado exitosamente
```

## 🧪 Pruebas y Demo

### Paso 1: Preparar el entorno

```bash
# 1. Verificar que el servidor esté corriendo
python manage.py runserver

# 2. Exponer con ngrok (en otra terminal)
ngrok http 8000

# 3. Actualizar BASE_URL en .env con la URL de ngrok
BASE_URL=https://xxxxx.ngrok-free.app
```

### Paso 2: Crear preferencia de pago

```bash
# PowerShell
$body = @{
    appointmentId = "apt_test_001"
    contactId = "TU_CONTACT_ID_GHL"  # 👈 Usa un contactId real de GHL
    amount = 50.00
    description = "Prueba de pago - Demo Día 3"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/payments/create" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

**Resultado esperado:**
```json
{
  "success": true,
  "init_point": "https://www.mercadopago.com.pe/checkout/v1/redirect?pref_id=xxxxx",
  "preference_id": "xxxxx",
  "payment_id": null,
  "status": "pending"
}
```

### Paso 3: Realizar el pago (Sandbox)

1. Copiar el `init_point` del paso anterior
2. Abrir en el navegador
3. Usar datos de prueba:
   - **Tarjeta:** `5031 7557 3453 0604`
   - **Vencimiento:** `11/25`
   - **CVV:** `123`
   - **Titular:** `APRO`

### Paso 4: Verificar en GHL

1. Ir a tu subcuenta de GoHighLevel
2. Buscar el contacto por `contactId`
3. ✅ Verificar que aparezca el tag `pago_confirmado`

### Paso 5: Verificar logs

```bash
# Ver logs en tiempo real
tail -f webhook.log
```

**Logs esperados:**
```
[2025-10-15 10:30:15] payments.views INFO [PAYMENT] ID: 123456789 | Status: approved | Amount: $50.0 | Payer: test_user_123456@testuser.com
[2025-10-15 10:30:15] payments.views INFO [PAYMENT] Saved: 123456789 -> approved
[2025-10-15 10:30:15] payments.views INFO [GHL] Intentando agregar tag a contacto TU_CONTACT_ID_GHL
[2025-10-15 10:30:16] payments.views INFO [GHL] ✓ Tag agregado exitosamente: Tag 'pago_confirmado' agregado exitosamente
```

## 📊 Verificar Estado de Pago

**Endpoint:** `GET /payments/status/{appointmentId}`

```bash
# PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/payments/status/apt_test_001"
```

**Response:**
```json
{
  "appointment_id": "apt_test_001",
  "contact_id": "TU_CONTACT_ID_GHL",
  "preference_id": "xxxxx",
  "payment_id": "123456789",
  "amount": 50.00,
  "status": "approved",
  "created_at": "2025-10-15T10:25:00"
}
```

## 🔍 Estructura de Archivos

```
ghl-payments/
├── backend/                    # Configuración Django
├── payments/                   # App de pagos
│   ├── views.py               # ⭐ Endpoints + Webhook
│   └── ghl_service.py         # ⭐ Servicio GHL API
├── docs/                       # 📚 Documentación
├── tests/                      # 🧪 Scripts de prueba
├── scripts/                    # 🚀 Scripts de demo
├── logs/                       # 📋 Archivos de log
├── screenshots/                # 📸 Capturas
├── .env                        # 🔐 Variables de entorno
├── db.sqlite3                  # Base de datos
├── manage.py                   # CLI Django
├── README.md                   # Este archivo
└── STRUCTURE.md               # Documentación de estructura
```

📖 **Ver estructura completa:** [STRUCTURE.md](STRUCTURE.md)

## 📚 Documentación Adicional

- **[STRUCTURE.md](STRUCTURE.md)** - Estructura completa del proyecto
- **[docs/GUIA_RAPIDA.md](docs/GUIA_RAPIDA.md)** - Demo en 5 minutos
- **[docs/COMANDOS_RAPIDOS.md](docs/COMANDOS_RAPIDOS.md)** - Comandos listos para usar
- **[docs/FLUJO.md](docs/FLUJO.md)** - Diagrama de flujo visual
- **[docs/RESUMEN_FINAL.md](docs/RESUMEN_FINAL.md)** - Resumen completo

---

## 🎯 Opciones de Implementación

### Opción A: Tags (Implementado ✅)

```python
from payments.ghl_service import add_tag_to_contact

result = add_tag_to_contact(contact_id, "pago_confirmado")
```

**Ventajas:**
- ✅ Simple y visible en la interfaz de GHL
- ✅ Fácil de filtrar contactos
- ✅ No requiere configuración previa

### Opción B: Custom Fields (Disponible)

```python
from payments.ghl_service import update_custom_field

result = update_custom_field(contact_id, "payment_status", "paid")
```

**Ventajas:**
- ✅ Más control sobre el valor
- ✅ Puede almacenar múltiples estados
- ⚠️ Requiere crear el custom field en GHL primero

## 📝 Capturas de Pantalla para Demo

### 1. Crear Preferencia
![Captura 1](screenshots/1_create_preference.png)
*Request POST y respuesta con init_point*

### 2. Pago en Sandbox
![Captura 2](screenshots/2_payment_sandbox.png)
*Pantalla de pago de MercadoPago*

### 3. Logs del Webhook
![Captura 3](screenshots/3_webhook_logs.png)
*Logs mostrando la actualización exitosa en GHL*

### 4. Tag en GoHighLevel
![Captura 4](screenshots/4_ghl_tag.png)
*Contacto con tag "pago_confirmado" en GHL*

## 🐛 Troubleshooting

### Error: "GHL_TOKEN no configurado"
- Verificar que `.env` tenga `GHL_TOKEN` definido
- Reiniciar el servidor después de modificar `.env`

### Error 401 en GHL
- Verificar que el token sea válido
- Verificar que sea un Private Token de la subcuenta correcta

### Tag no aparece en GHL
- Verificar que el `contactId` sea correcto
- Revisar logs en `webhook.log`
- Verificar que el pago tenga `status="approved"`

### Webhook no se recibe
- Verificar que ngrok esté corriendo
- Verificar que `BASE_URL` en `.env` sea la URL de ngrok
- Verificar que MercadoPago tenga la URL del webhook correcta

## 📚 Recursos

- [MercadoPago API Docs](https://www.mercadopago.com.pe/developers/es/docs)
- [GoHighLevel API Docs](https://highlevel.stoplight.io/)
- [Django Docs](https://docs.djangoproject.com/)

## ✅ Checklist de Demo

- [ ] Variables de entorno configuradas
- [ ] Servidor Django corriendo
- [ ] ngrok exponiendo el servidor
- [ ] BASE_URL actualizado en .env
- [ ] Contacto de prueba creado en GHL
- [ ] Preferencia de pago creada
- [ ] Pago realizado en sandbox
- [ ] Logs verificados
- [ ] Tag visible en GHL
- [ ] Capturas tomadas
- [ ] README actualizado

---

**Autor:** Backend Developer - ReflexoPerú  
**Fecha:** Octubre 2025  
**Versión:** Día 3 - Integración GHL completada ✅
