# DIAGNÓSTICO Y SOLUCIÓN DE WEBHOOKS - Mercado Pago

## 🔍 **Diagnóstico Actual:**

### ✅ **Lo que está funcionando:**
1. ✅ Servidor Django corriendo en `http://0.0.0.0:8000`
2. ✅ Ngrok activo con URL: `https://e08c5324f489.ngrok-free.app`
3. ✅ Creación de preferencias de pago OK
4. ✅ Base de datos guardando pagos

### ❌ **Problema Identificado:**
- **Ngrok gratis muestra una página de advertencia** antes de permitir el acceso
- Esto impide que Mercado Pago envíe webhooks correctamente
- Error: 502 Bad Gateway o página HTML en lugar de JSON

---

## 🛠️ **SOLUCIONES:**

### **Opción 1: Usar ngrok sin página de advertencia (RECOMENDADO)**

1. **Deten ngrok actual:**
   ```powershell
   Get-Process ngrok | Stop-Process -Force
   ```

2. **Inicia ngrok con configuración especial:**
   ```powershell
   ngrok http 8000 --domain=e08c5324f489.ngrok-free.app
   ```
   
   O si no funciona, usa:
   ```powershell
   ngrok http 8000 --host-header=rewrite
   ```

### **Opción 2: Actualizar a ngrok Pro (Más confiable)**
- URL: https://ngrok.com/pricing
- Sin página de advertencia
- Dominios personalizados
- Más estable para webhooks

### **Opción 3: Usar otro túnel (Alternativas gratuitas)**

**Localtunnel:**
```powershell
npm install -g localtunnel
lt --port 8000 --subdomain reflexoperu
```

**Cloudflare Tunnel (GRATIS Y SIN LÍMITES):**
```powershell
# Descargar cloudflared
# Ejecutar:
cloudflared tunnel --url http://localhost:8000
```

---

## 🔧 **Verificar que todo funcione:**

### 1. **Verificar servidor local:**
```powershell
curl http://localhost:8000/webhooks/mp
```
Debe responder (aunque sea con error JSON, no HTML)

### 2. **Verificar túnel:**
Abre en navegador: `https://TU-URL-NGROK/webhooks/mp`

### 3. **Probar webhook manualmente:**
```powershell
python test_webhook_local.py
```

### 4. **Ver logs en tiempo real:**
```powershell
Get-Content logs\webhook.log -Wait -Tail 20
```

---

## 📋 **Checklist de Configuración:**

- [ ] Servidor Django corriendo en puerto 8000
- [ ] Ngrok/túnel apuntando a puerto 8000  
- [ ] Variable `BASE_URL` en `.env` actualizada
- [ ] Webhook URL configurada en Mercado Pago: `{BASE_URL}/webhooks/mp`
- [ ] CSRF deshabilitado para webhook (`@csrf_exempt`)

---

## 🎯 **Configuración Actual en Mercado Pago:**

Tu webhook debe estar configurado en:
https://www.mercadopago.com.pe/developers/panel/webhooks

**URL del Webhook:**
```
https://e08c5324f489.ngrok-free.app/webhooks/mp
```

**Eventos a escuchar:**
- ✅ payment
- ✅ merchant_order

---

## 🔥 **SOLUCIÓN RÁPIDA (AHORA MISMO):**

1. **Reinicia ngrok con bypass:**
```powershell
Get-Process ngrok | Stop-Process -Force
ngrok http 8000 --scheme=http,https
```

2. **Copia la nueva URL HTTPS que aparece**

3. **Actualiza `.env`:**
```
BASE_URL=https://NUEVA-URL-AQUI.ngrok-free.app
```

4. **Reinicia Django** (Ctrl+C en el terminal y vuelve a ejecutar)

5. **Actualiza webhook en Mercado Pago:**
   - Ve a: https://www.mercadopago.com.pe/developers/panel/webhooks
   - Edita la URL del webhook
   - Guarda

6. **Haz un pago de prueba**

7. **Verifica logs:**
```powershell
Get-Content logs\webhook.log -Wait -Tail 20
```

---

## 📊 **Comandos Útiles:**

**Ver estado de ngrok:**
```powershell
curl http://127.0.0.1:4040/api/tunnels | ConvertFrom-Json | Select-Object -ExpandProperty tunnels
```

**Ver procesos corriendo:**
```powershell
Get-Process | Where-Object {$_.ProcessName -match "python|ngrok"}
```

**Limpiar todo y empezar de nuevo:**
```powershell
Get-Process python,ngrok -ErrorAction SilentlyContinue | Stop-Process -Force
cd C:\Users\Ignacio\Downloads\ghl-payments
python manage.py runserver 0.0.0.0:8000
# En otra terminal:
ngrok http 8000
```
