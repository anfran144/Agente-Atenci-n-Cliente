"""
Script to generate embeddings for FAQs and Products

This script:
1. Fetches all FAQs and Products from the database
2. Generates embeddings using the RAG service
3. Stores embeddings in faqs_embeddings and products_embeddings tables

Run this after seeding data to populate the embeddings tables.
"""

from database import get_supabase_client
from rag_service import RAGService
from typing import List, Dict, Any


def generate_faq_embeddings(rag_service: RAGService, supabase_client):
    """Generate embeddings for all FAQs"""
    print("Generating FAQ embeddings...")
    
    # Fetch all FAQs
    result = supabase_client.table("faqs").select("*").execute()
    faqs = result.data
    
    print(f"Found {len(faqs)} FAQs")
    
    embeddings_data = []
    for faq in faqs:
        # Combine question and answer for better semantic search
        text = f"{faq['question']} {faq['answer']}"
        
        # Generate embedding
        embedding = rag_service.generate_embedding(text)
        
        embeddings_data.append({
            "faq_id": faq["id"],
            "tenant_id": faq["tenant_id"],
            "embedding": embedding
        })
    
    # Insert embeddings in batches
    if embeddings_data:
        # Delete existing embeddings first
        supabase_client.table("faqs_embeddings").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        
        # Insert new embeddings
        result = supabase_client.table("faqs_embeddings").insert(embeddings_data).execute()
        print(f"Inserted {len(result.data)} FAQ embeddings")
    
    return len(embeddings_data)


def generate_product_embeddings(rag_service: RAGService, supabase_client):
    """Generate embeddings for all products"""
    print("Generating product embeddings...")
    
    # Fetch all active products
    result = supabase_client.table("products").select("*").eq("is_active", True).execute()
    products = result.data
    
    print(f"Found {len(products)} products")
    
    embeddings_data = []
    for product in products:
        # Combine name, description, and category for better semantic search
        text_parts = [product['name']]
        if product.get('description'):
            text_parts.append(product['description'])
        if product.get('category'):
            text_parts.append(product['category'])
        
        text = " ".join(text_parts)
        
        # Generate embedding
        embedding = rag_service.generate_embedding(text)
        
        embeddings_data.append({
            "product_id": product["id"],
            "tenant_id": product["tenant_id"],
            "embedding": embedding
        })
    
    # Insert embeddings in batches
    if embeddings_data:
        # Delete existing embeddings first
        supabase_client.table("products_embeddings").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        
        # Insert new embeddings
        result = supabase_client.table("products_embeddings").insert(embeddings_data).execute()
        print(f"Inserted {len(result.data)} product embeddings")
    
    return len(embeddings_data)


def main():
    """Main function to generate all embeddings"""
    print("Starting embedding generation...")
    
    # Initialize clients
    supabase_client = get_supabase_client()
    rag_service = RAGService(supabase_client)
    
    # Generate embeddings
    faq_count = generate_faq_embeddings(rag_service, supabase_client)
    product_count = generate_product_embeddings(rag_service, supabase_client)
    
    print(f"\nEmbedding generation complete!")
    print(f"Total FAQs: {faq_count}")
    print(f"Total Products: {product_count}")


if __name__ == "__main__":
    main()
