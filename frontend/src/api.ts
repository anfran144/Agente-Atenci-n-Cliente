import { Tenant, ChatResponse, TenantStats, NetworkInsightsResponse, User } from './types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Custom error class for API errors with user-friendly messages
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public userMessage?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Handle API response errors with user-friendly messages
 */
async function handleResponse<T>(response: Response, context: string): Promise<T> {
  if (!response.ok) {
    let errorMessage = `Failed to ${context}`;
    let userMessage = errorMessage;

    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMessage = errorData.detail;
        userMessage = errorData.detail;
      }
    } catch {
      // If we can't parse the error response, use status-based messages
      switch (response.status) {
        case 400:
          userMessage = 'Invalid request. Please check your input and try again.';
          break;
        case 401:
          userMessage = 'Authentication required. Please log in again.';
          break;
        case 403:
          userMessage = 'You do not have permission to access this resource.';
          break;
        case 404:
          userMessage = 'The requested resource was not found.';
          break;
        case 500:
          userMessage = 'Server error. Please try again later.';
          break;
        case 503:
          userMessage = 'Service temporarily unavailable. Please try again in a moment.';
          break;
        default:
          userMessage = `An error occurred (${response.status}). Please try again.`;
      }
    }

    throw new ApiError(errorMessage, response.status, userMessage);
  }

  try {
    return await response.json();
  } catch (error) {
    throw new ApiError(
      'Failed to parse response',
      response.status,
      'Received invalid data from server. Please try again.'
    );
  }
}

/**
 * Validate input before sending to API
 */
function validateMessage(message: string): { valid: boolean; error?: string } {
  if (!message || message.trim().length === 0) {
    return { valid: false, error: 'Message cannot be empty' };
  }

  if (message.length > 5000) {
    return { valid: false, error: 'Message is too long (maximum 5000 characters)' };
  }

  // Check for potentially malicious content
  const suspiciousPatterns = [/<script/i, /javascript:/i, /onerror=/i];
  if (suspiciousPatterns.some(pattern => pattern.test(message))) {
    return { valid: false, error: 'Message contains invalid content' };
  }

  return { valid: true };
}

export const api = {
  /**
   * Fetch all active tenants
   */
  async getTenants(): Promise<Tenant[]> {
    try {
      const response = await fetch(`${API_URL}/tenants`, {
        signal: AbortSignal.timeout(10000), // 10 second timeout
      });
      return await handleResponse<Tenant[]>(response, 'fetch tenants');
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ApiError(
          'Request timeout',
          408,
          'The request took too long. Please check your connection and try again.'
        );
      }
      throw new ApiError(
        'Network error',
        0,
        'Unable to connect to the server. Please check your internet connection.'
      );
    }
  },

  /**
   * Fetch all active users
   */
  async getUsers(): Promise<User[]> {
    try {
      const response = await fetch(`${API_URL}/users`, {
        signal: AbortSignal.timeout(10000),
      });
      return await handleResponse<User[]>(response, 'fetch users');
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(
        'Network error',
        0,
        'Unable to connect to the server. Please check your internet connection.'
      );
    }
  },

  /**
   * Send a chat message to the agent
   */
  async sendMessage(
    tenantId: string,
    message: string,
    conversationId?: string,
    userId?: string
  ): Promise<ChatResponse> {
    // Validate input
    const validation = validateMessage(message);
    if (!validation.valid) {
      throw new ApiError('Validation error', 400, validation.error);
    }

    if (!tenantId || tenantId.trim().length === 0) {
      throw new ApiError('Validation error', 400, 'Tenant ID is required');
    }

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tenant_id: tenantId,
          message: message.trim(),
          conversation_id: conversationId,
          user_id: userId,
        }),
        signal: AbortSignal.timeout(30000), // 30 second timeout for chat
      });
      return await handleResponse<ChatResponse>(response, 'send message');
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ApiError(
          'Request timeout',
          408,
          'The agent is taking too long to respond. Please try again.'
        );
      }
      throw new ApiError(
        'Network error',
        0,
        'Unable to send message. Please check your internet connection.'
      );
    }
  },

  /**
   * Get statistics for a specific tenant
   */
  async getStats(tenantId: string): Promise<TenantStats> {
    if (!tenantId || tenantId.trim().length === 0) {
      throw new ApiError('Validation error', 400, 'Tenant ID is required');
    }

    try {
      const response = await fetch(`${API_URL}/stats/${tenantId}`, {
        signal: AbortSignal.timeout(15000), // 15 second timeout
      });
      return await handleResponse<TenantStats>(response, 'fetch statistics');
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ApiError(
          'Request timeout',
          408,
          'Loading statistics took too long. Please try again.'
        );
      }
      throw new ApiError(
        'Network error',
        0,
        'Unable to load statistics. Please check your internet connection.'
      );
    }
  },

  /**
   * Get network insights across all tenants
   */
  async getNetworkInsights(): Promise<NetworkInsightsResponse> {
    try {
      const response = await fetch(`${API_URL}/network-insights`, {
        signal: AbortSignal.timeout(15000), // 15 second timeout
      });
      return await handleResponse<NetworkInsightsResponse>(response, 'fetch network insights');
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ApiError(
          'Request timeout',
          408,
          'Loading insights took too long. Please try again.'
        );
      }
      throw new ApiError(
        'Network error',
        0,
        'Unable to load network insights. Please check your internet connection.'
      );
    }
  },
};
