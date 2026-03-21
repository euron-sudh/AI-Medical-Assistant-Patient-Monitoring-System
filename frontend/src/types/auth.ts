export type UserRole = "patient" | "doctor" | "nurse" | "admin";

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  phone?: string;
  is_active: boolean;
  is_verified: boolean;
  last_login_at?: string;
  created_at?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  confirm_password: string;
  first_name: string;
  last_name: string;
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
