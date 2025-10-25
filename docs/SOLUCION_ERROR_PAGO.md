# 🔴 SOLUCIÓN: "Algo salió mal... No pudimos procesar tu pago"

## ❌ PROBLEMA IDENTIFICADO

Estás usando **credenciales de PRODUCCIÓN** pero intentando pagar con **tarjetas de prueba**.

### ¿Por qué falla?

```
Credenciales de PRODUCCIÓN → Solo aceptan tarjetas REALES
Tarjetas de PRUEBA        → Solo funcionan con credenciales TEST
```

**NUNCA funcionarán juntas** ❌

---

## ✅ SOLUCIÓN: Cambiar a Credenciales de TEST

### Paso 1: Obtener Credenciales de Prueba

1. Ve a: https://www.mercadopago.com.pe/developers/panel/app

2. Inicia sesión con tu cuenta de Mercado Pago

3. Selecciona tu aplicación (o crea una si no tienes)

4. En el menú lateral, haz clic en **"Credenciales de prueba"**
   
   ```
   ┌─────────────────────┐
   │ ► Credenciales      │
   │   ├─ Producción     │ ← NO uses estas
   │   └─ Prueba         │ ← USA ESTAS ✅
   └─────────────────────┘
   ```

5. Copia las credenciales que comienzan con `TEST-`:
   - Access Token: `TEST-123456789...`
   - Public Key: `TEST-abc123...`

---

### Paso 2: Actualizar el archivo .env

1. Abre el archivo `.env` en tu proyecto

2. Reemplaza las credenciales:

   ```env
   # ANTES (Producción - ❌)
   MP_ACCESS_TOKEN=APP_USR-69220608395747-101320-f50556285c304e3167b9616cdc03639a-2923809231
   MP_PUBLIC_KEY=APP_USR-e20c16c9-f9df-4b14-b56a-3b758c9c85f4
   
   # DESPUÉS (Prueba - ✅)
   MP_ACCESS_TOKEN=TEST-1234567890123456-123456-abcdefghijklmnopqrstuvwxyz-123456789
   MP_PUBLIC_KEY=TEST-12345678-1234-1234-1234-123456789abc
   ```

3. Guarda el archivo `.env`

---

### Paso 3: Reiniciar Django

1. En la terminal donde corre Django, presiona `Ctrl + C`

2. Vuelve a iniciar el servidor:
   ```powershell
   python manage.py runserver 0.0.0.0:8000
   ```

---

### Paso 4: Probar con Tarjetas de Prueba

Ahora puedes usar estas **tarjetas de prueba**:

#### ✅ Tarjetas que APRUEBAN el pago:

| Tipo | Número | CVV | Vencimiento |
|------|--------|-----|-------------|
| **Visa** | 4509 9535 6623 3704 | 123 | 11/25 |
| **Mastercard** | 5031 7557 3453 0604 | 123 | 11/25 |
| **Amex** | 3711 803032 57522 | 1234 | 11/25 |

#### ❌ Tarjetas que RECHAZAN el pago (para probar):

| Número | Razón del rechazo |
|--------|-------------------|
| 4000 1234 5678 9010 | Fondos insuficientes |
| 5031 4332 1540 6351 | Rechazado por el banco |

#### 📝 Datos de prueba:

- **Nombre:** Cualquier nombre
- **DNI/CPF:** 12345678
- **CVV:** 123 (o 1234 para Amex)
- **Vencimiento:** Cualquier fecha futura

---

## 🎯 VERIFICAR QUE TODO FUNCIONE

### Checklist:

1. [ ] Credenciales de TEST copiadas del panel de MP
2. [ ] Archivo `.env` actualizado con credenciales TEST
3. [ ] Django reiniciado
4. [ ] Probar pago con tarjeta de prueba: **4509 9535 6623 3704**
5. [ ] Pago debe completarse exitosamente ✅

---

## 📋 Si aún falla:

1. **Ejecuta el diagnóstico:**
   ```powershell
   python scripts\diagnose_mp.py
   ```

2. **Verifica los logs:**
   ```powershell
   Get-Content logs\webhook.log -Wait -Tail 20
   ```

3. **Verifica que Django se reinició correctamente:**
   - Debe mostrar: "Starting development server at http://0.0.0.0:8000/"

---

## 🚀 Cuando vayas a PRODUCCIÓN

Cuando quieras usar pagos REALES:

1. Cambia a **Credenciales de Producción** (las que comienzan con `APP_USR-`)
2. Actualiza el `.env`
3. Reinicia Django
4. Usa **tarjetas REALES** con saldo
5. ⚠️ **Los cargos serán REALES** - Ten cuidado

---

## 📚 Recursos Útiles

- 🔗 Panel de Apps: https://www.mercadopago.com.pe/developers/panel/app
- 🔗 Tarjetas de Prueba: https://www.mercadopago.com.pe/developers/es/docs/checkout-pro/additional-content/test-cards
- 🔗 Documentación: https://www.mercadopago.com.pe/developers/es/docs

---

## 💡 TIP: Diferencia entre TEST y PRODUCCIÓN

```
╔══════════════════════════════════════════════════════════╗
║                   CREDENCIALES TEST                      ║
╠══════════════════════════════════════════════════════════╣
║ ✅ Para desarrollo y pruebas                             ║
║ ✅ Usa tarjetas de prueba (ficticias)                    ║
║ ✅ No se hacen cargos reales                             ║
║ ✅ Puedes probar cuantas veces quieras                   ║
║ ✅ Comienzan con: TEST-                                  ║
╚══════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════╗
║                CREDENCIALES PRODUCCIÓN                   ║
╠══════════════════════════════════════════════════════════╣
║ ⚠️  Para clientes reales                                 ║
║ ⚠️  Usa tarjetas REALES con saldo                        ║
║ ⚠️  Los cargos son REALES                                ║
║ ⚠️  El dinero entra a tu cuenta de MP                    ║
║ ⚠️  Comienzan con: APP_USR-                              ║
╚══════════════════════════════════════════════════════════╝
```

---

## ✨ ¡Listo!

Después de seguir estos pasos, tus pagos deberían funcionar correctamente. 

Si tienes dudas, ejecuta:
```powershell
python scripts\diagnose_mp.py
```
