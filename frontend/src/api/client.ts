const API_BASE =
  import.meta.env.VITE_API_BASE_URL || '/api/v1';
export interface UserProfile {
  id: number;
  username: string;
  full_name: string;
  role: 'salesman' | 'admin' | 'production' | 'accountant' | 'owner';
  phone?: string;
  is_active: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  role: 'salesman' | 'admin' | 'production' | 'accountant' | 'owner';
  full_name: string;
  username: string;
}

export async function loginUser(username: string, password: string): Promise<LoginResponse> {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData.toString()
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(error.detail || 'Invalid credentials');
  }

  return res.json();
}

export async function registerUser(payload: {
  username: string;
  password: string;
  full_name: string;
  role: string;
  phone?: string;
}): Promise<LoginResponse> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Registration failed' }));
    throw new Error(error.detail || 'Registration failed');
  }

  return res.json();
}

export async function resetPassword(payload: {
  username: string;
  new_password: string;
  phone?: string;
}): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE}/auth/forgot-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Password reset failed' }));
    throw new Error(error.detail || 'Password reset failed');
  }

  return res.json();
}

export async function fetchCurrentUser(token: string): Promise<UserProfile> {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!res.ok) {
    throw new Error('Failed to fetch profile');
  }

  return res.json();
}
