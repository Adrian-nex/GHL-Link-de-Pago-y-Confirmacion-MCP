# 🔄 Pull Requests para el Proyecto

## 📋 Instrucciones para Crear PRs

### 1. **CI/CD Infrastructure**
- **Rama**: `feature/ci-setup`
- **URL**: https://github.com/Adrian-nex/GHL-Link-de-Pago-y-Confirmacion-MCP/compare/main...feature/ci-setup
- **Título**: `feat: Setup CI/CD Infrastructure`
- **Descripción**: Establece la infraestructura de CI/CD con Black, isort, flake8, pytest

### 2. **Core Models**
- **Rama**: `feature/core-models`
- **URL**: https://github.com/Adrian-nex/GHL-Link-de-Pago-y-Confirmacion-MCP/compare/main...feature/core-models
- **Título**: `feat: Add Core Models and Django Configuration`
- **Descripción**: Agrega modelos Payment y WebhookEvent con configuración Django

### 3. **API Endpoints**
- **Rama**: `feature/api`
- **URL**: https://github.com/Adrian-nex/GHL-Link-de-Pago-y-Confirmacion-MCP/compare/main...feature/api
- **Título**: `feat: Add API Endpoints and Admin Interface`
- **Descripción**: Agrega endpoints de API y interfaz de administración

### 4. **Frontend Interface**
- **Rama**: `feature/frontend`
- **URL**: https://github.com/Adrian-nex/GHL-Link-de-Pago-y-Confirmacion-MCP/compare/main...feature/frontend
- **Título**: `feat: Add Frontend Interface`
- **Descripción**: Agrega interfaz web completa con HTML/CSS/JS

### 5. **Webhooks System**
- **Rama**: `feature/webhooks`
- **URL**: https://github.com/Adrian-nex/GHL-Link-de-Pago-y-Confirmacion-MCP/compare/main...feature/webhooks
- **Título**: `feat: Add Webhooks System and Services`
- **Descripción**: Agrega sistema de webhooks con procesamiento asíncrono

### 6. **Documentation**
- **Rama**: `feature/docs`
- **URL**: https://github.com/Adrian-nex/GHL-Link-de-Pago-y-Confirmacion-MCP/compare/main...feature/docs
- **Título**: `feat: Add Comprehensive Documentation and Tests`
- **Descripción**: Agrega documentación completa y tests unitarios

## 🚀 Pasos para Crear PRs

1. **Ir a GitHub**: https://github.com/Adrian-nex/GHL-Link-de-Pago-y-Confirmacion-MCP/pulls
2. **Click "New Pull Request"**
3. **Seleccionar rama base**: `main`
4. **Seleccionar rama feature**: `feature/xxx`
5. **Agregar título y descripción**
6. **Click "Create Pull Request"**

## 📊 Orden Recomendado de Merge

1. **CI/CD** → Base para todo
2. **Core Models** → Fundación del sistema
3. **API Endpoints** → Funcionalidad backend
4. **Frontend** → Interfaz de usuario
5. **Webhooks** → Integración avanzada
6. **Documentation** → Finalización

## ✅ Checklist para cada PR

- [ ] Código revisado
- [ ] Tests pasando
- [ ] Sin conflictos
- [ ] Documentación actualizada
- [ ] CI/CD funcionando
