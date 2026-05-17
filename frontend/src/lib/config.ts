/**
 * Single source of truth for the API base URL.
 * Both api.ts and AuthContext.tsx import from here,
 * which avoids a circular dependency between those two files.
 */
export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
).replace(/\/+$/, '');