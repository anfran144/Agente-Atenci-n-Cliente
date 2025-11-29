-- Update embedding dimensions to match sentence-transformers model
-- all-mpnet-base-v2 produces 768-dimensional embeddings

-- Drop existing indexes
DROP INDEX IF EXISTS idx_faqs_embeddings_vector;
DROP INDEX IF EXISTS idx_products_embeddings_vector;

-- Alter embedding columns to use 768 dimensions
ALTER TABLE faqs_embeddings ALTER COLUMN embedding TYPE vector(768);
ALTER TABLE products_embeddings ALTER COLUMN embedding TYPE vector(768);

-- Recreate vector similarity search indexes
CREATE INDEX idx_faqs_embeddings_vector ON faqs_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_products_embeddings_vector ON products_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
