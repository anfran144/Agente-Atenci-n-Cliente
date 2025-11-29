// User models
export interface User {
  id: string;
  name: string;
  email: string;
  phone?: string;
  preferences: Record<string, any>;
  is_active: boolean;
}

// Tenant models
export interface Tenant {
  id: string;
  name: string;
  type: string;
  is_active: boolean;
}

// Chat models
export interface Message {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  timestamp: Date;
  intent?: string;
}

export interface OrderSummary {
  products: Array<{
    product_id?: string;
    name: string;
    quantity: number;
    unit_price?: number;
    price?: number;
  }>;
  total: number;
}

export interface ChatRequest {
  tenant_id: string;
  conversation_id?: string;
  message: string;
  user_id?: string;
  customer_id?: string;
}

export interface ChatResponse {
  conversation_id: string;
  response: string;
  intent: string;
  requires_confirmation: boolean;
  order_summary?: OrderSummary;
}

// Stats models
export interface HourStat {
  hour: number;
  count: number;
}

export interface ProductStat {
  product_id: string;
  name: string;
  mentions: number;
}

export interface CommonQuestion {
  question: string;
  frequency: number;
}

export interface TenantStats {
  tenant_id: string;
  peak_hours: HourStat[];
  top_products: ProductStat[];
  common_questions: CommonQuestion[];
}

// Network insights models
export interface GlobalPattern {
  pattern: string;
  confidence: number;
  business_types?: string[];
}

export interface NetworkInsightsResponse {
  patterns: GlobalPattern[];
  generated_at: string;
}
