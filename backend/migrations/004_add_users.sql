-- ============================================
-- MIGRACIÓN: AGREGAR TABLA DE USUARIOS
-- Ejecutar en Supabase Dashboard → SQL Editor
-- ============================================

-- 1. Crear tabla de usuarios
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- 2. Agregar columna user_id a conversations (si no existe)
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id);

-- 3. Crear tabla para preferencias aprendidas del usuario
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id),
    preference_type VARCHAR(100) NOT NULL, -- 'favorite_product', 'dietary_restriction', 'preferred_time', etc.
    preference_value TEXT NOT NULL,
    confidence FLOAT DEFAULT 0.5, -- Qué tan seguro está el sistema de esta preferencia
    learned_from_count INT DEFAULT 1, -- Cuántas veces se detectó
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 4. Crear índices
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_tenant ON user_preferences(user_id, tenant_id);

-- 5. Insertar 5 usuarios de ejemplo
INSERT INTO users (id, name, email, phone, preferences) VALUES
    ('11111111-1111-1111-1111-111111111111', 'María García', 'maria@example.com', '+56912345678', 
     '{"language": "es", "notifications": true}'),
    ('22222222-2222-2222-2222-222222222222', 'Juan Pérez', 'juan@example.com', '+56923456789', 
     '{"language": "es", "notifications": true}'),
    ('33333333-3333-3333-3333-333333333333', 'Ana Rodríguez', 'ana@example.com', '+56934567890', 
     '{"language": "es", "notifications": false}'),
    ('44444444-4444-4444-4444-444444444444', 'Carlos López', 'carlos@example.com', '+56945678901', 
     '{"language": "es", "notifications": true}'),
    ('55555555-5555-5555-5555-555555555555', 'Sofía Martínez', 'sofia@example.com', '+56956789012', 
     '{"language": "es", "notifications": true}')
ON CONFLICT (email) DO NOTHING;

-- 6. Verificar usuarios creados
SELECT id, name, email FROM users ORDER BY name;
