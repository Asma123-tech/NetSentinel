/**
 * Token storage utilities.
 * Kept in a separate file so both api.ts and AuthContext.tsx
 * can import getStoredToken() without creating a circular dependency.
 */

const TOKEN_KEY   = 'ns_access_token';
const REFRESH_KEY = 'ns_refresh_token';

export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function storeTokens(access: string, refresh: string): void {
  localStorage.setItem(TOKEN_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}