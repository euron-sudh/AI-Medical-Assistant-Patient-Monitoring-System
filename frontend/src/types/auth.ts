export type UserRole = "patient" | "doctor" | "nurse" | "admin";

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  phone?: string;
  isActive: boolean;
  isVerified: boolean;
  lastLoginAt?: string;
  createdAt: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  accessToken: string;
  refreshToken: string;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  confirmPassword: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  phone?: string;
}

export interface RegisterResponse {
  message: string;
  user: User;
}

export interface AuthError {
  error: string;
  message: string;
  details?: Record<string, string[]>;
}
