# Frontend - Multi-Tenant Customer Agent

Interfaz de usuario React para el agente de atención al cliente.

## Stack

- React 18 + TypeScript
- TailwindCSS
- Axios

## Configuración

```bash
# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env
# Editar .env con la URL del backend

# Ejecutar en desarrollo
npm start
```

## Estructura

```
src/
├── components/
│   ├── TenantSelector.tsx   # Selector de negocio
│   ├── UserSelector.tsx     # Selector de usuario
│   ├── RoleSelector.tsx     # Selector de rol (cliente/admin)
│   ├── ChatInterface.tsx    # Interfaz de chat
│   ├── Dashboard.tsx        # Estadísticas e insights
│   └── ErrorBoundary.tsx    # Manejo de errores
├── api.ts                   # Cliente API
├── types.ts                 # Tipos TypeScript
└── App.tsx                  # Componente principal
```

## Scripts

- `npm start` - Servidor de desarrollo
- `npm run build` - Build de producción
- `npm test` - Ejecutar tests
