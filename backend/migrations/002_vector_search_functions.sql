-- RPC function for FAQ vector similarity search
-- This function performs cosine similarity search on FAQ embeddings
-- filtered by tenant_id
-- Using vector(768) to match sentence-transformers/all-mpnet-base-v2
CREATE OR REPLACE FUNCTION match_faqs(
    query_embedding vector(768),
    match_tenant_id uuid,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    faq_id uuid,
    tenant_id uuid,
    question text,
    answer text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        fe.id,
        fe.faq_id,
        fe.tenant_id,
        f.question,
        f.answer,
        1 - (fe.embedding <=> query_embedding) as similarity
    FROM faqs_embeddings fe
    JOIN faqs f ON f.id = fe.faq_id
    WHERE fe.tenant_id = match_tenant_id
    ORDER BY fe.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- RPC function for Product vector similarity search
-- This function performs cosine similarity search on product embeddings
-- filtered by tenant_id
-- Using vector(768) to match sentence-transformers/all-mpnet-base-v2
CREATE OR REPLACE FUNCTION match_products(
    query_embedding vector(768),
    match_tenant_id uuid,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    product_id uuid,
    tenant_id uuid,
    name varchar(255),
    description text,
    category varchar(100),
    price decimal(10, 2),
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        pe.id,
        pe.product_id,
        pe.tenant_id,
        p.name,
        p.description,
        p.category,
        p.price,
        1 - (pe.embedding <=> query_embedding) as similarity
    FROM products_embeddings pe
    JOIN products p ON p.id = pe.product_id
    WHERE pe.tenant_id = match_tenant_id
        AND p.is_active = true
    ORDER BY pe.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
