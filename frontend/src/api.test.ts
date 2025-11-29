import { ApiError } from './api';

describe('API Error Handling', () => {
  describe('ApiError', () => {
    it('creates an ApiError with user message', () => {
      const error = new ApiError('Technical error', 500, 'User-friendly message');
      
      expect(error.message).toBe('Technical error');
      expect(error.statusCode).toBe(500);
      expect(error.userMessage).toBe('User-friendly message');
      expect(error.name).toBe('ApiError');
    });

    it('ApiError extends Error', () => {
      const error = new ApiError('Test', 400, 'User message');
      expect(error instanceof Error).toBe(true);
      expect(error instanceof ApiError).toBe(true);
    });

    it('ApiError can be thrown and caught', () => {
      const throwError = () => {
        throw new ApiError('Technical', 404, 'Not found');
      };

      expect(throwError).toThrow(ApiError);
      
      try {
        throwError();
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError);
        expect((error as ApiError).statusCode).toBe(404);
        expect((error as ApiError).userMessage).toBe('Not found');
      }
    });

    it('ApiError with different status codes', () => {
      const error400 = new ApiError('Bad request', 400, 'Invalid input');
      const error401 = new ApiError('Unauthorized', 401, 'Please log in');
      const error500 = new ApiError('Server error', 500, 'Try again later');

      expect(error400.statusCode).toBe(400);
      expect(error401.statusCode).toBe(401);
      expect(error500.statusCode).toBe(500);
    });
  });
});
