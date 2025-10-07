export type Role = 'user' | 'assistant' | 'system';

export interface Message {
  id: string;
  userId: string;
  role: Role;
  content: string;
  createdAt: string;
}

export interface Memory {
  id: string;
  userId: string;
  content: string;
  source?: string;
  tags?: string;
  createdAt: string;
}

export interface UserProfile {
  id: string;
  email: string;
  fullName?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: 'bearer';
}
