# 🧪 GUÍA COMPLETA PARA PROBAR WEBHOOKS DE MERCADO PAGO

## ✅ Estado Actual del Sistema

### Configuración Verificada
- ✅ **Webhook URL**: `https://187aad8613e0.ngrok-free.app/webhooks/mp`
- ✅ **Servidor**: Respondiendo correctamente (Status 405 en GET, 200 en POST)
- ✅ **Base de datos**: 13 pagos registrados (todos pendientes)
- ✅ **Mercado Pago**: Credenciales configuradas

### Scripts Disponibles
1. `scripts/test_webhook_complete.py` - Pruebas del webhook
2. `scripts/monitor_webhook.py` - Monitor en tiempo real
3. `scripts/test_payment_guide.py` - Guía paso a paso

---

## 🚀 PASOS PARA PROBAR EL WEBHOOK COMPLETO

### Paso 1: Preparar el Entorno

#### Terminal 1: Iniciar el Servidor Django
```powershell
python manage.py runserver
```

#### Terminal 2: Iniciar el Monitor de Webhooks
```powershell
python scripts\monitor_webhook.py
```

Este monitor te mostrará en tiempo real:
- 🆕 Nuevos pagos creados
- 🔄 Actualizaciones de status
- 💳 Payment IDs asignados
- ✅ Pagos aprobados/rechazados

---

### Paso 2: Crear un Pago de Prueba

1. **Abre tu navegador en**: `http://localhost:8000`

2. **Ingresa los siguientes datos**:
   - **Appointment ID**: `cita_test_014` (o el siguiente sugerido)
   - **Contact ID**: `test_contact_001` (o un ID real de GHL)
   - **Monto**: `50.00`
   - **Descripción**: `Prueba de webhook MP`

3. **Haz clic en** "Crear Link de Pago"

4. **Haz clic en** "Ir a Pagar" (te llevará a Mercado Pago)

---

### Paso 3: Completar el Pago en Mercado Pago

#### 🟢 Para Simular un PAGO APROBADO:
```
Número de tarjeta: 5031 7557 3453 0604
Vencimiento: 11/25
CVV: 123
Nombre del titular: APRO
DNI: 12345678
Email: test@test.com
```

#### 🔴 Para Simular un PAGO RECHAZADO:
```
Número de tarjeta: 5031 4332 1540 6351
Vencimiento: 11/25
CVV: 123
Nombre del titular: OTHE
DNI: 12345678
Email: test@test.com
```

---

### Paso 4: Observar los Webhooks

En la **Terminal 2** (monitor) verás algo como esto:

```
🔔 CAMBIO DETECTADO - 11:23:45
================================================================================

🆕 NUEVO PAGO CREADO
✅ Payment #60
   Cita: cita_test_014
   Contact: test_contact_001
   Amount: S/ 50.00
   Status: pending
   Preference ID: 2923809231-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   Payment ID: N/A
   Created: 2025-10-20 11:23:45

================================================================================

🔄 PAGO ACTUALIZADO - 11:23:52
================================================================================

📊 Status: pending → approved
💳 Payment ID: N/A → 87654321098

✅ Payment #60
   Cita: cita_test_014
   Contact: test_contact_001
   Amount: S/ 50.00
   Status: approved
   Payment ID: 87654321098
   Created: 2025-10-20 11:23:45

================================================================================
```

---

## 🔄 Flujo Completo de Webhooks

Cuando realizas un pago, Mercado Pago envía estas notificaciones:

### 1️⃣ Notificación: `payment.created`
- **Cuándo**: Inmediatamente al crear el pago
- **Qué hace el webhook**:
  - Recibe el `payment_id`
  - Consulta la API de MP para obtener detalles
  - Actualiza el `Payment` en la DB con `payment_id` y `status: pending`
- **Qué verás en el monitor**: "🆕 NUEVO PAGO CREADO"

### 2️⃣ Notificación: `payment.updated`
- **Cuándo**: Cuando el pago se procesa (aprobado/rechazado)
- **Qué hace el webhook**:
  - Actualiza el `status` del pago
  - Si `status = 'approved'` → Agrega el tag "pago_confirmado" en GHL
- **Qué verás en el monitor**: "🔄 PAGO ACTUALIZADO" con el nuevo status

### 3️⃣ Notificación: `merchant_order`
- **Cuándo**: Confirmación final de la orden
- **Qué hace el webhook**:
  - Obtiene información completa de la orden
  - Lista de pagos asociados
  - Confirma el monto total
- **Qué verás en el monitor**: Puede aparecer como actualización adicional

---

## 📊 Comandos Útiles

### Ver los últimos pagos
```powershell
python scripts\monitor_webhook.py recent 10
```

### Probar el webhook con simulaciones
```powershell
python scripts\test_webhook_complete.py
```

### Ver la guía completa
```powershell
python scripts\test_payment_guide.py
```

### Ver logs del servidor Django
El servidor muestra logs detallados en la terminal donde ejecutaste `runserver`:
- `[PAYMENT]` - Notificaciones de pago
- `[MO]` - Notificaciones de merchant order
- `[GHL]` - Operaciones con GoHighLevel

---

## 🔍 Verificar que el Webhook Funciona

### ✅ Indicadores de que TODO está bien:

1. **En el monitor verás**:
   - 🆕 Creación del pago con status "pending"
   - 🔄 Actualización a "approved" (si usaste tarjeta APRO)
   - 💳 Payment ID asignado

2. **En la web (refresca la página)**:
   - El pago aparece en la lista
   - El status cambió de "pending" a "approved"
   - El Payment ID está visible

3. **En GoHighLevel** (si el contact_id es válido):
   - Se agregó el tag "pago_confirmado" al contacto

### ❌ Si algo no funciona:

1. **El webhook no recibe notificaciones**:
   - Verifica que ngrok esté corriendo
   - Verifica que la URL en `.env` coincida con la de ngrok
   - Verifica que el servidor Django esté corriendo

2. **El pago no se actualiza**:
   - Revisa los logs del servidor Django
   - Verifica las credenciales de MP en `.env`
   - Verifica que el `preference_id` exista en la DB

3. **El tag no se agrega en GHL**:
   - Verifica el `GHL_TOKEN` en `.env`
   - Verifica que el `contact_id` sea válido
   - Revisa los logs `[GHL]` en el servidor

---

## 💡 Consejos

1. **Usa siempre el monitor**: Te permite ver exactamente qué está pasando
2. **Revisa los logs**: El servidor Django muestra información detallada
3. **Prueba ambas tarjetas**: Aprobada y rechazada para ver ambos flujos
4. **No cierres el monitor**: Déjalo corriendo mientras haces pruebas

---

## 📝 Próximos Pasos

1. ✅ Probar con pago aprobado
2. ✅ Probar con pago rechazado
3. ✅ Verificar que el tag se agregue en GHL
4. ✅ Probar con un contact_id real de GHL
5. ✅ Verificar que el sistema maneje webhooks duplicados

---

## 🎯 Resumen

El webhook está **completamente funcional** y listo para recibir notificaciones de Mercado Pago. 

**Para probarlo ahora mismo**:

1. Abre 2 terminales
2. Terminal 1: `python manage.py runserver`
3. Terminal 2: `python scripts\monitor_webhook.py`
4. Abre el navegador en `http://localhost:8000`
5. Crea un pago y complétalo con la tarjeta APRO
6. ¡Observa cómo llegan los webhooks en tiempo real! 🎉

---

**Fecha de actualización**: 2025-10-20
**Estado**: ✅ Sistema listo para pruebas
