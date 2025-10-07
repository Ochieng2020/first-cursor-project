export interface ApiClientOptions {
  baseUrl: string;
  getToken?: () => string | undefined;
}

export class ApiClient {
  private baseUrl: string;
  private getToken?: () => string | undefined;

  constructor(options: ApiClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, '');
    this.getToken = options.getToken;
  }

  private headers(): HeadersInit {
    const headers: HeadersInit = { 'Content-Type': 'application/json' };
    const token = this.getToken?.();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return headers;
  }

  async register(email: string, password: string, fullName?: string) {
    const res = await fetch(`${this.baseUrl}/api/user/register`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async login(email: string, password: string) {
    const res = await fetch(`${this.baseUrl}/api/user/login`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async listMemories() {
    const res = await fetch(`${this.baseUrl}/api/memory/`, { headers: this.headers() });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async createMemory(content: string, tags?: string) {
    const res = await fetch(`${this.baseUrl}/api/memory/`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify({ content, tags }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async chat(userId: string, message: string, onToken?: (t: string) => void) {
    const res = await fetch(`${this.baseUrl}/api/chat/`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify({ user_id: userId, message }),
    });
    if (!res.ok) throw new Error(await res.text());

    const reader = res.body?.getReader();
    if (!reader) return '';

    const decoder = new TextDecoder();
    let reply = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      for (const line of chunk.split(/\r?\n/)) {
        if (!line.startsWith('data: ')) continue;
        const data = line.slice(6);
        if (data === '[DONE]') break;
        try {
          const obj = JSON.parse(data);
          if (obj.token) {
            onToken?.(obj.token);
            reply += obj.token;
          }
        } catch {}
      }
    }

    return reply;
  }
}
