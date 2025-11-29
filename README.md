# Multi-Tenant Customer Service Agent

Agente conversacional multi-tenant para atención al cliente, construido con LangGraph, FastAPI y React.

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│                    React + TypeScript                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Tenant    │  │    Chat     │  │       Dashboard         │  │
│  │  Selector   │  │  Interface  │  │   (Stats & Insights)    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                  │
│                    FastAPI + LangGraph                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Agent Workflow                         │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │    │
│  │  │ Classify │→ │   FAQ    │→ │  Order   │→ │ Review  │  │    │
│  │  │  Intent  │  │ Handler  │  │ Handler  │  │ Handler │  │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐      │
│  │ RAG Service │  │ Repository  │  │  Stats Aggregator   │      │
│  │ (Embeddings)│  │  (CRUD)     │  │  (Network Insights) │      │
│  └─────────────┘  └─────────────┘  └─────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        SUPABASE                                  │
│  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌─────────┐ ┌───────────┐  │
│  │ Tenants │ │ Products │ │ Orders │ │ Reviews │ │ Embeddings│  │
│  └─────────┘ └──────────┘ └────────┘ └─────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Inicio Rápido

### Prerrequisitos

- Python 3.10+
- Node.js 18+
- Cuenta en [Supabase](https://supabase.com) (gratis)
- API Key de [Groq](https://console.groq.com) (gratis)

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/multi-tenant-customer-agent.git
cd multi-tenant-customer-agent
```

### 2. Configurar Supabase

1. Crear un proyecto en [Supabase](https://supabase.com)
2. Ejecutar las migraciones SQL en orden:
   - `backend/migrations/001_initial_schema.sql`
   - `backend/migrations/002_vector_search_functions.sql`
   - `backend/migrations/003_update_embedding_dimensions.sql`
   - `backend/migrations/004_add_users.sql`
   - `backend/migrations/005_add_conversation_metadata.sql`

### 3. Configurar variables de entorno

**Backend** (`backend/.env`):
```env
GROQ_API_KEY=gsk_tu_api_key
GROQ_MODEL=llama-3.3-70b-versatile
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_anon_key
SUPABASE_SERVICE_KEY=tu_service_key
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000
```

**Frontend** (`frontend/.env`):
```env
REACT_APP_API_URL=http://localhost:8000
```

### 4. Instalar dependencias

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 5. Cargar datos de prueba

```bash
cd backend
python seed_data.py
python generate_embeddings.py
```

### 6. Ejecutar

```bash
# Terminal 1 - Backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm start
```

Abrir http://localhost:3000

## 📦 Dependencias Principales

### Backend
| Paquete | Versión | Propósito |
|---------|---------|-----------|
| FastAPI | 0.109.0 | Framework web API |
| LangGraph | 0.0.20 | Orquestación del agente |
| LangChain | 0.1.6 | Integración LLM |
| langchain-groq | 0.0.1 | Conector Groq |
| sentence-transformers | 2.3.1 | Embeddings locales |
| Supabase | 2.3.4 | Cliente base de datos |

### Frontend
| Paquete | Versión | Propósito |
|---------|---------|-----------|
| React | 18.x | Framework UI |
| TypeScript | 4.x | Tipado estático |
| TailwindCSS | 3.x | Estilos |
| Axios | 1.x | Cliente HTTP |

## 🤖 Documentación del Agente

### Flujo de Conversación

```
Usuario → Clasificar Intent → Handler Específico → Generar Respuesta → Usuario
```

### Intents Soportados

| Intent | Descripción | Ejemplo |
|--------|-------------|---------|
| `faq` | Preguntas frecuentes | "¿Cuál es el horario?" |
| `order_create` | Crear pedido nuevo | "Quiero 2 pizzas" |
| `order_update` | Modificar pedido existente | "Agrégame una bebida" |
| `complaint` | Quejas | "La comida llegó fría" |
| `review` | Reseñas positivas | "Excelente servicio" |
| `other` | No clasificado | "Hola" |

### Características del Agente

- **Multi-tenant**: Aislamiento de datos por negocio
- **RAG**: Respuestas basadas en FAQs y productos del tenant
- **Contexto de pedido**: Mantiene el carrito entre mensajes
- **Personalización**: Saluda por nombre a usuarios registrados
- **Validación de inventario**: Verifica stock antes de confirmar
- **Horarios de negocio**: Valida si el negocio está abierto

### Persistencia de Estado

El agente mantiene el estado del pedido (`order_draft`) en el campo `metadata` de la tabla `conversations`, permitiendo que el usuario haga preguntas intermedias sin perder su carrito.

## 📁 Estructura del Proyecto

```
├── backend/
│   ├── agent.py              # Workflow LangGraph (clasificación + handlers)
│   ├── main.py               # API FastAPI (endpoints)
│   ├── repository.py         # Acceso a datos (CRUD)
│   ├── rag_service.py        # Servicio RAG (embeddings + búsqueda)
│   ├── models.py             # Modelos Pydantic
│   ├── database.py           # Conexión Supabase
│   ├── seed_data.py          # Datos de prueba
│   ├── generate_embeddings.py # Generar embeddings
│   ├── stats_aggregator.py   # Agregación de estadísticas
│   ├── scheduled_stats_job.py # Job programado de stats
│   ├── migrations/           # Scripts SQL (ejecutar en orden)
│   └── tests/                # Tests unitarios e integración
├── frontend/
│   ├── src/
│   │   ├── components/    # Componentes React
│   │   ├── services/      # Servicios API
│   │   └── App.tsx        # Componente principal
│   └── public/
├── docker-compose.yml     # Orquestación Docker
└── README.md
```

## 🐳 Docker

```bash
docker-compose up --build
```

## 📊 API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/tenants` | Listar tenants activos |
| POST | `/chat` | Enviar mensaje al agente |
| GET | `/stats/{tenant_id}` | Estadísticas del tenant |
| GET | `/network-insights` | Insights globales |
| GET | `/users` | Listar usuarios |

## 🧪 Tests

```bash
cd backend
pytest tests/
```

### Cobertura de Tests

- `test_agent_foundation.py` - Tests del workflow del agente
- `test_intent_classification.py` - Clasificación de intents
- `test_order_*.py` - Flujo de pedidos
- `test_faq_integration.py` - Integración FAQ + RAG
- `test_review_*.py` - Manejo de reseñas
- `test_stats_*.py` - Estadísticas
- `test_network_insights*.py` - Insights de red

## 📄 Licencia

MIT
