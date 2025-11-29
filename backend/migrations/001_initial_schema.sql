-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Tenants table
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC',
    config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Products table
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    price DECIMAL(10, 2) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Inventory items table
CREATE TABLE inventory_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    unit VARCHAR(50) DEFAULT 'unit',
    updated_at TIMESTAMP DEFAULT NOW()
);

-- FAQs table
CREATE TABLE faqs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    channel VARCHAR(50) DEFAULT 'web',
    customer_id VARCHAR(255),
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender VARCHAR(20) NOT NULL CHECK (sender IN ('user', 'agent')),
    text TEXT NOT NULL,
    intent VARCHAR(50),
    created_at TIMESTAMP NOT NULL
);

-- Orders table
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    total_amount DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Order items table
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL
);

-- Reviews table
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    source VARCHAR(50) DEFAULT 'chat',
    requires_attention BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tenant stats table
CREATE TABLE tenant_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    hour INTEGER NOT NULL CHECK (hour >= 0 AND hour <= 23),
    interactions_count INTEGER DEFAULT 0,
    orders_count INTEGER DEFAULT 0,
    top_product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, date, hour)
);

-- Demand signals table (for network insights)
CREATE TABLE demand_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    confidence_score DECIMAL(3, 2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Vector embeddings for FAQs
CREATE TABLE faqs_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    faq_id UUID NOT NULL REFERENCES faqs(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Vector embeddings for Products
CREATE TABLE products_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for multi-tenant queries
CREATE INDEX idx_products_tenant_id ON products(tenant_id);
CREATE INDEX idx_products_tenant_active ON products(tenant_id, is_active);
CREATE INDEX idx_inventory_tenant_id ON inventory_items(tenant_id);
CREATE INDEX idx_inventory_tenant_product ON inventory_items(tenant_id, product_id);
CREATE INDEX idx_faqs_tenant_id ON faqs(tenant_id);
CREATE INDEX idx_conversations_tenant_id ON conversations(tenant_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_orders_tenant_id ON orders(tenant_id);
CREATE INDEX idx_orders_conversation_id ON orders(conversation_id);
CREATE INDEX idx_reviews_tenant_id ON reviews(tenant_id);
CREATE INDEX idx_reviews_created_at ON reviews(created_at DESC);
CREATE INDEX idx_tenant_stats_tenant_date ON tenant_stats(tenant_id, date, hour);
CREATE INDEX idx_faqs_embeddings_tenant ON faqs_embeddings(tenant_id);
CREATE INDEX idx_products_embeddings_tenant ON products_embeddings(tenant_id);

-- Vector similarity search indexes
CREATE INDEX idx_faqs_embeddings_vector ON faqs_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_products_embeddings_vector ON products_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
