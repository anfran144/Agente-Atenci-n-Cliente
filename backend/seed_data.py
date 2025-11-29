"""
Seed script for multi-tenant customer agent
Creates 5 tenants with products, FAQs, inventory, and reviews
"""
import uuid
from datetime import datetime
from database import init_db

# Tenant configurations
TENANTS = [
    {
        "name": "La Trattoria Italiana",
        "type": "restaurant",
        "timezone": "America/Santiago",
        "config": {
            "business_hours": {"monday": "12:00-23:00", "tuesday": "12:00-23:00", 
                             "wednesday": "12:00-23:00", "thursday": "12:00-23:00",
                             "friday": "12:00-00:00", "saturday": "12:00-00:00", "sunday": "12:00-22:00"},
            "address": "Av. Providencia 1234, Santiago",
            "payment_methods": ["efectivo", "tarjeta", "transferencia"]
        }
    },
    {
        "name": "Sushi Zen",
        "type": "restaurant",
        "timezone": "America/Santiago",
        "config": {
            "business_hours": {"monday": "closed", "tuesday": "18:00-23:00", 
                             "wednesday": "18:00-23:00", "thursday": "18:00-23:00",
                             "friday": "18:00-00:00", "saturday": "13:00-00:00", "sunday": "13:00-22:00"},
            "address": "Las Condes 5678, Santiago",
            "payment_methods": ["efectivo", "tarjeta", "transferencia", "cripto"]
        }
    },
    {
        "name": "El Asador Criollo",
        "type": "restaurant",
        "timezone": "America/Santiago",
        "config": {
            "business_hours": {"monday": "12:00-16:00,19:00-23:00", "tuesday": "12:00-16:00,19:00-23:00",
                             "wednesday": "12:00-16:00,19:00-23:00", "thursday": "12:00-16:00,19:00-23:00",
                             "friday": "12:00-00:00", "saturday": "12:00-00:00", "sunday": "12:00-23:00"},
            "address": "Bellavista 910, Santiago",
            "payment_methods": ["efectivo", "tarjeta"]
        }
    },
    {
        "name": "Panadería Doña Rosa",
        "type": "bakery",
        "timezone": "America/Santiago",
        "config": {
            "business_hours": {"monday": "07:00-20:00", "tuesday": "07:00-20:00",
                             "wednesday": "07:00-20:00", "thursday": "07:00-20:00",
                             "friday": "07:00-20:00", "saturday": "07:00-21:00", "sunday": "08:00-14:00"},
            "address": "Ñuñoa 2345, Santiago",
            "payment_methods": ["efectivo", "tarjeta"]
        }
    },
    {
        "name": "MiniMarket Express",
        "type": "minimarket",
        "timezone": "America/Santiago",
        "config": {
            "business_hours": {"monday": "08:00-23:00", "tuesday": "08:00-23:00",
                             "wednesday": "08:00-23:00", "thursday": "08:00-23:00",
                             "friday": "08:00-23:00", "saturday": "08:00-23:00", "sunday": "09:00-22:00"},
            "address": "Macul 3456, Santiago",
            "payment_methods": ["efectivo", "tarjeta", "transferencia"]
        }
    }
]

# Products by tenant type
RESTAURANT_ITALIAN_PRODUCTS = [
    {"name": "Pizza Margherita", "description": "Tomate, mozzarella, albahaca", "category": "pizzas", "price": 12000},
    {"name": "Pizza Pepperoni", "description": "Tomate, mozzarella, pepperoni", "category": "pizzas", "price": 13500},
    {"name": "Pasta Carbonara", "description": "Pasta con salsa carbonara", "category": "pastas", "price": 11000},
    {"name": "Lasagna Bolognesa", "description": "Lasagna con carne y bechamel", "category": "pastas", "price": 12500},
    {"name": "Risotto ai Funghi", "description": "Risotto con hongos", "category": "risottos", "price": 13000},
    {"name": "Ensalada Caprese", "description": "Tomate, mozzarella, albahaca", "category": "ensaladas", "price": 8500},
    {"name": "Bruschetta", "description": "Pan tostado con tomate y albahaca", "category": "entradas", "price": 6500},
    {"name": "Tiramisu", "description": "Postre italiano con café", "category": "postres", "price": 5500},
    {"name": "Panna Cotta", "description": "Postre de crema", "category": "postres", "price": 5000},
    {"name": "Vino Tinto Casa", "description": "Vino de la casa", "category": "bebidas", "price": 15000},
    {"name": "Agua Mineral", "description": "Agua con o sin gas", "category": "bebidas", "price": 2000},
    {"name": "Espresso", "description": "Café italiano", "category": "bebidas", "price": 2500},
]

RESTAURANT_SUSHI_PRODUCTS = [
    {"name": "Sushi Roll California", "description": "Cangrejo, palta, pepino", "category": "rolls", "price": 9500},
    {"name": "Sushi Roll Philadelphia", "description": "Salmón, queso crema", "category": "rolls", "price": 10500},
    {"name": "Sushi Roll Spicy Tuna", "description": "Atún picante", "category": "rolls", "price": 11000},
    {"name": "Nigiri Salmón", "description": "2 piezas de salmón", "category": "nigiri", "price": 6500},
    {"name": "Nigiri Atún", "description": "2 piezas de atún", "category": "nigiri", "price": 7000},
    {"name": "Sashimi Mix", "description": "Variedad de pescados", "category": "sashimi", "price": 14000},
    {"name": "Tempura Camarón", "description": "Camarones fritos", "category": "tempura", "price": 8500},
    {"name": "Gyoza", "description": "Empanaditas japonesas", "category": "entradas", "price": 6000},
    {"name": "Edamame", "description": "Porotos de soya", "category": "entradas", "price": 4500},
    {"name": "Mochi", "description": "Postre de arroz", "category": "postres", "price": 4000},
    {"name": "Té Verde", "description": "Té japonés", "category": "bebidas", "price": 2500},
    {"name": "Sake", "description": "Licor de arroz", "category": "bebidas", "price": 8000},
    {"name": "Ramune", "description": "Gaseosa japonesa", "category": "bebidas", "price": 3000},
]

RESTAURANT_ASADOR_PRODUCTS = [
    {"name": "Bife de Chorizo", "description": "Corte argentino 300g", "category": "carnes", "price": 16000},
    {"name": "Asado de Tira", "description": "Costillas 400g", "category": "carnes", "price": 14000},
    {"name": "Entraña", "description": "Corte de entraña 250g", "category": "carnes", "price": 15000},
    {"name": "Choripán", "description": "Chorizo en pan", "category": "sandwiches", "price": 5500},
    {"name": "Provoleta", "description": "Queso provolone a la parrilla", "category": "entradas", "price": 6500},
    {"name": "Empanadas de Carne", "description": "3 unidades", "category": "entradas", "price": 4500},
    {"name": "Ensalada Mixta", "description": "Lechuga, tomate, cebolla", "category": "ensaladas", "price": 4000},
    {"name": "Papas Fritas", "description": "Porción grande", "category": "acompañamientos", "price": 3500},
    {"name": "Flan Casero", "description": "Con dulce de leche", "category": "postres", "price": 4500},
    {"name": "Vino Malbec", "description": "Vino argentino", "category": "bebidas", "price": 18000},
    {"name": "Cerveza Artesanal", "description": "500ml", "category": "bebidas", "price": 4500},
    {"name": "Gaseosa", "description": "Coca-Cola, Sprite, Fanta", "category": "bebidas", "price": 2500},
]

BAKERY_PRODUCTS = [
    {"name": "Pan Amasado", "description": "Pan tradicional chileno", "category": "panes", "price": 800},
    {"name": "Hallulla", "description": "Pan redondo", "category": "panes", "price": 600},
    {"name": "Marraqueta", "description": "Pan francés", "category": "panes", "price": 500},
    {"name": "Pan Integral", "description": "Pan de molde integral", "category": "panes", "price": 2500},
    {"name": "Croissant", "description": "Croissant de mantequilla", "category": "pastelería", "price": 1800},
    {"name": "Empanada de Pino", "description": "Carne, cebolla, huevo", "category": "empanadas", "price": 2000},
    {"name": "Empanada de Queso", "description": "Queso derretido", "category": "empanadas", "price": 1800},
    {"name": "Torta de Mil Hojas", "description": "Porción", "category": "tortas", "price": 3500},
    {"name": "Kuchen de Manzana", "description": "Porción", "category": "tortas", "price": 3000},
    {"name": "Alfajor", "description": "Con manjar", "category": "dulces", "price": 1200},
    {"name": "Sopaipilla", "description": "Frita o al horno", "category": "dulces", "price": 500},
    {"name": "Café con Leche", "description": "Taza grande", "category": "bebidas", "price": 2000},
    {"name": "Jugo Natural", "description": "Naranja o zanahoria", "category": "bebidas", "price": 2500},
]

MINIMARKET_PRODUCTS = [
    {"name": "Leche Entera 1L", "description": "Leche fresca", "category": "lácteos", "price": 1200},
    {"name": "Pan de Molde", "description": "Pan blanco", "category": "panadería", "price": 1800},
    {"name": "Huevos Docena", "description": "12 unidades", "category": "lácteos", "price": 3500},
    {"name": "Arroz 1kg", "description": "Arroz grado 1", "category": "abarrotes", "price": 1500},
    {"name": "Fideos 500g", "description": "Pasta italiana", "category": "abarrotes", "price": 1200},
    {"name": "Aceite 1L", "description": "Aceite vegetal", "category": "abarrotes", "price": 2800},
    {"name": "Azúcar 1kg", "description": "Azúcar blanca", "category": "abarrotes", "price": 1400},
    {"name": "Café Instantáneo", "description": "100g", "category": "bebidas", "price": 3500},
    {"name": "Galletas Surtidas", "description": "Paquete 200g", "category": "snacks", "price": 1800},
    {"name": "Papas Fritas Bolsa", "description": "150g", "category": "snacks", "price": 1500},
    {"name": "Cerveza Lata", "description": "355ml", "category": "bebidas", "price": 1200},
    {"name": "Gaseosa 1.5L", "description": "Coca-Cola, Sprite, Fanta", "category": "bebidas", "price": 1800},
    {"name": "Agua Mineral 500ml", "description": "Con o sin gas", "category": "bebidas", "price": 800},
    {"name": "Jabón de Manos", "description": "Líquido 250ml", "category": "limpieza", "price": 2200},
    {"name": "Papel Higiénico 4 rollos", "description": "Doble hoja", "category": "limpieza", "price": 3000},
]

# FAQs by tenant type
RESTAURANT_ITALIAN_FAQS = [
    {"question": "¿Cuál es el horario de atención?", "answer": "Estamos abiertos de lunes a jueves de 12:00 a 23:00, viernes y sábado de 12:00 a 00:00, y domingos de 12:00 a 22:00."},
    {"question": "¿Dónde están ubicados?", "answer": "Nos encontramos en Av. Providencia 1234, Santiago."},
    {"question": "¿Qué métodos de pago aceptan?", "answer": "Aceptamos efectivo, tarjetas de crédito/débito y transferencias bancarias."},
    {"question": "¿Tienen opciones vegetarianas?", "answer": "Sí, tenemos varias opciones vegetarianas como Pizza Margherita, Ensalada Caprese, Bruschetta y Risotto ai Funghi."},
    {"question": "¿Tienen opciones sin gluten?", "answer": "Sí, podemos preparar algunas pizzas y pastas con masa sin gluten. Por favor indícalo al hacer tu pedido."},
    {"question": "¿Manejan alérgenos?", "answer": "Nuestros platos pueden contener gluten, lácteos, huevo y frutos secos. Consulta con nosotros sobre alergias específicas."},
    {"question": "¿Hacen delivery?", "answer": "Sí, hacemos delivery a través de nuestra plataforma y apps de delivery asociadas."},
    {"question": "¿Tienen menú del día?", "answer": "Sí, de lunes a viernes tenemos menú ejecutivo de 12:00 a 16:00 con entrada, plato de fondo y postre."},
    {"question": "¿Aceptan reservas?", "answer": "Sí, aceptamos reservas por teléfono o a través de nuestra web para grupos de 4 o más personas."},
    {"question": "¿Tienen estacionamiento?", "answer": "Tenemos convenio con estacionamiento cercano en Av. Providencia 1250."},
]

RESTAURANT_SUSHI_FAQS = [
    {"question": "¿Cuál es el horario de atención?", "answer": "Abrimos de martes a viernes de 18:00 a 23:00, sábados de 13:00 a 00:00 y domingos de 13:00 a 22:00. Cerramos los lunes."},
    {"question": "¿Dónde están ubicados?", "answer": "Estamos en Las Condes 5678, Santiago."},
    {"question": "¿Qué métodos de pago aceptan?", "answer": "Aceptamos efectivo, tarjetas, transferencias y criptomonedas (Bitcoin, Ethereum)."},
    {"question": "¿El pescado es fresco?", "answer": "Sí, trabajamos con pescado fresco que llega diariamente de proveedores certificados."},
    {"question": "¿Tienen opciones vegetarianas?", "answer": "Sí, tenemos rolls vegetarianos con palta, pepino, zanahoria y otros vegetales."},
    {"question": "¿Manejan alérgenos?", "answer": "Nuestros platos contienen pescado, mariscos, soya, gluten y sésamo. Consulta por alergias específicas."},
    {"question": "¿Tienen opciones sin gluten?", "answer": "Podemos preparar algunos rolls sin salsa de soya (que contiene gluten) usando tamari sin gluten."},
    {"question": "¿Hacen delivery?", "answer": "Sí, hacemos delivery propio y también estamos en apps de delivery."},
    {"question": "¿Tienen barra de sushi?", "answer": "Sí, tenemos barra donde puedes ver al chef preparar tu pedido."},
    {"question": "¿Aceptan reservas?", "answer": "Sí, recomendamos reservar especialmente los fines de semana."},
]

RESTAURANT_ASADOR_FAQS = [
    {"question": "¿Cuál es el horario de atención?", "answer": "Abrimos de lunes a jueves de 12:00 a 16:00 y de 19:00 a 23:00. Viernes y sábados de 12:00 a 00:00, domingos de 12:00 a 23:00."},
    {"question": "¿Dónde están ubicados?", "answer": "Nos encontramos en Bellavista 910, Santiago."},
    {"question": "¿Qué métodos de pago aceptan?", "answer": "Aceptamos efectivo y tarjetas de crédito/débito."},
    {"question": "¿Qué tipo de carnes tienen?", "answer": "Tenemos cortes argentinos como bife de chorizo, asado de tira, entraña y más, todos a la parrilla."},
    {"question": "¿Tienen opciones vegetarianas?", "answer": "Tenemos ensaladas, provoleta y algunos acompañamientos vegetarianos, pero somos principalmente un asador."},
    {"question": "¿Manejan alérgenos?", "answer": "Nuestros platos pueden contener gluten (en panes y empanadas) y lácteos. Las carnes son libres de alérgenos comunes."},
    {"question": "¿Hacen delivery?", "answer": "Sí, hacemos delivery de nuestros platos principales."},
    {"question": "¿Tienen parrilla a la vista?", "answer": "Sí, puedes ver nuestra parrilla en funcionamiento desde el comedor."},
    {"question": "¿Aceptan reservas?", "answer": "Sí, recomendamos reservar especialmente los fines de semana."},
    {"question": "¿Tienen estacionamiento?", "answer": "Hay estacionamiento público en la calle y estacionamientos cercanos."},
]

BAKERY_FAQS = [
    {"question": "¿Cuál es el horario de atención?", "answer": "Abrimos de lunes a viernes de 07:00 a 20:00, sábados de 07:00 a 21:00 y domingos de 08:00 a 14:00."},
    {"question": "¿Dónde están ubicados?", "answer": "Estamos en Ñuñoa 2345, Santiago."},
    {"question": "¿Qué métodos de pago aceptan?", "answer": "Aceptamos efectivo y tarjetas de crédito/débito."},
    {"question": "¿El pan es del día?", "answer": "Sí, todo nuestro pan es horneado diariamente en el local."},
    {"question": "¿Tienen opciones sin gluten?", "answer": "Sí, tenemos pan sin gluten que horneamos en días específicos. Consulta disponibilidad."},
    {"question": "¿Manejan alérgenos?", "answer": "Nuestros productos contienen gluten, huevo, lácteos y pueden tener trazas de frutos secos."},
    {"question": "¿Hacen tortas por encargo?", "answer": "Sí, hacemos tortas personalizadas con 48 horas de anticipación."},
    {"question": "¿Tienen café?", "answer": "Sí, servimos café, té y jugos naturales."},
    {"question": "¿Venden pan congelado?", "answer": "Sí, vendemos masa de empanadas y algunos panes para hornear en casa."},
    {"question": "¿Tienen estacionamiento?", "answer": "Hay estacionamiento en la calle frente al local."},
]

MINIMARKET_FAQS = [
    {"question": "¿Cuál es el horario de atención?", "answer": "Abrimos de lunes a sábado de 08:00 a 23:00 y domingos de 09:00 a 22:00."},
    {"question": "¿Dónde están ubicados?", "answer": "Nos encontramos en Macul 3456, Santiago."},
    {"question": "¿Qué métodos de pago aceptan?", "answer": "Aceptamos efectivo, tarjetas de crédito/débito y transferencias bancarias."},
    {"question": "¿Hacen delivery?", "answer": "Sí, hacemos delivery para compras sobre $10.000 en un radio de 2km."},
    {"question": "¿Tienen productos frescos?", "answer": "Sí, tenemos lácteos, huevos, pan y algunos vegetales frescos."},
    {"question": "¿Venden alcohol?", "answer": "Sí, vendemos cerveza, vino y licores. Se requiere ser mayor de 18 años."},
    {"question": "¿Tienen productos de limpieza?", "answer": "Sí, tenemos una sección de productos de limpieza e higiene personal."},
    {"question": "¿Aceptan devoluciones?", "answer": "Sí, aceptamos devoluciones de productos no perecibles con boleta dentro de 7 días."},
    {"question": "¿Tienen estacionamiento?", "answer": "Tenemos 3 espacios de estacionamiento frente al local."},
    {"question": "¿Tienen productos sin gluten?", "answer": "Sí, tenemos una pequeña sección de productos sin gluten y sin lactosa."},
]

# Sample reviews
SAMPLE_REVIEWS = [
    {"rating": 5, "comment": "Excelente atención y comida deliciosa", "source": "chat"},
    {"rating": 5, "comment": "Muy buena calidad, volveré pronto", "source": "chat"},
    {"rating": 4, "comment": "Buena experiencia, solo un poco de demora", "source": "chat"},
    {"rating": 4, "comment": "Rico todo, precios justos", "source": "chat"},
    {"rating": 3, "comment": "Normal, nada extraordinario", "source": "chat"},
]

def seed_tenants(supabase):
    """Seed tenants table"""
    print("Seeding tenants...")
    tenant_ids = []
    
    for tenant_data in TENANTS:
        result = supabase.table("tenants").insert(tenant_data).execute()
        tenant_id = result.data[0]["id"]
        tenant_ids.append(tenant_id)
        print(f"  Created tenant: {tenant_data['name']} (ID: {tenant_id})")
    
    return tenant_ids

def seed_products_and_inventory(supabase, tenant_ids):
    """Seed products and inventory for all tenants"""
    print("\nSeeding products and inventory...")
    
    products_map = {
        0: RESTAURANT_ITALIAN_PRODUCTS,  # La Trattoria Italiana
        1: RESTAURANT_SUSHI_PRODUCTS,     # Sushi Zen
        2: RESTAURANT_ASADOR_PRODUCTS,    # El Asador Criollo
        3: BAKERY_PRODUCTS,                # Panadería Doña Rosa
        4: MINIMARKET_PRODUCTS             # MiniMarket Express
    }
    
    for idx, tenant_id in enumerate(tenant_ids):
        products = products_map[idx]
        print(f"  Seeding products for tenant {idx + 1}...")
        
        for product_data in products:
            # Insert product
            product_insert = {
                "tenant_id": tenant_id,
                **product_data
            }
            result = supabase.table("products").insert(product_insert).execute()
            product_id = result.data[0]["id"]
            
            # Insert inventory with random stock
            import random
            stock_quantity = random.randint(10, 100)
            inventory_insert = {
                "tenant_id": tenant_id,
                "product_id": product_id,
                "stock_quantity": stock_quantity,
                "unit": "unit"
            }
            supabase.table("inventory_items").insert(inventory_insert).execute()
        
        print(f"    Added {len(products)} products with inventory")

def seed_faqs(supabase, tenant_ids):
    """Seed FAQs for all tenants"""
    print("\nSeeding FAQs...")
    
    faqs_map = {
        0: RESTAURANT_ITALIAN_FAQS,
        1: RESTAURANT_SUSHI_FAQS,
        2: RESTAURANT_ASADOR_FAQS,
        3: BAKERY_FAQS,
        4: MINIMARKET_FAQS
    }
    
    for idx, tenant_id in enumerate(tenant_ids):
        faqs = faqs_map[idx]
        print(f"  Seeding FAQs for tenant {idx + 1}...")
        
        for faq_data in faqs:
            faq_insert = {
                "tenant_id": tenant_id,
                **faq_data
            }
            supabase.table("faqs").insert(faq_insert).execute()
        
        print(f"    Added {len(faqs)} FAQs")

def seed_reviews(supabase, tenant_ids):
    """Seed sample reviews for all tenants"""
    print("\nSeeding reviews...")
    
    for idx, tenant_id in enumerate(tenant_ids):
        print(f"  Seeding reviews for tenant {idx + 1}...")
        
        for review_data in SAMPLE_REVIEWS:
            review_insert = {
                "tenant_id": tenant_id,
                **review_data,
                "requires_attention": review_data["rating"] <= 2
            }
            supabase.table("reviews").insert(review_insert).execute()
        
        print(f"    Added {len(SAMPLE_REVIEWS)} reviews")

def main():
    """Main seeding function"""
    print("=" * 60)
    print("Starting database seeding for multi-tenant customer agent")
    print("=" * 60)
    
    # Initialize database connection
    supabase = init_db()
    
    try:
        # Seed tenants
        tenant_ids = seed_tenants(supabase)
        
        # Seed products and inventory
        seed_products_and_inventory(supabase, tenant_ids)
        
        # Seed FAQs
        seed_faqs(supabase, tenant_ids)
        
        # Seed reviews
        seed_reviews(supabase, tenant_ids)
        
        print("\n" + "=" * 60)
        print("Database seeding completed successfully!")
        print("=" * 60)
        print(f"\nSeeded data:")
        print(f"  - {len(TENANTS)} tenants")
        print(f"  - Products: 12 (Italian) + 13 (Sushi) + 12 (Asador) + 13 (Bakery) + 15 (Minimarket) = 65 total")
        print(f"  - 10 FAQs per tenant = 50 total")
        print(f"  - 5 reviews per tenant = 25 total")
        print(f"  - Inventory items for all products")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        raise

if __name__ == "__main__":
    main()
