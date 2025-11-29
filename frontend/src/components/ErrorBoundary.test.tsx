import { ApiError } from '../api';

describe('ErrorBoundary', () => {
  it('ApiError class works correctly', () => {
    const error = new ApiError('Technical message', 500, 'User message');
    
    expect(error.message).toBe('Technical message');
    expect(error.statusCode).toBe(500);
    expect(error.userMessage).toBe('User message');
    expect(error.name).toBe('ApiError');
    expect(error instanceof Error).toBe(true);
  });

  it('ApiError can be thrown and caught', () => {
    const throwError = () => {
      throw new ApiError('Test error', 404, 'Not found');
    };

    expect(throwError).toThrow(ApiError);
    
    try {
      throwError();
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).userMessage).toBe('Not found');
    }
  });
});
