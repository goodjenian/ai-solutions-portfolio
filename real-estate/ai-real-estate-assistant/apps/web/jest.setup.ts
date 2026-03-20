import "@testing-library/jest-dom";

type ResponseInitLike = {
  status?: number;
  statusText?: string;
  headers?: HeadersInit;
};

class PolyfilledResponse {
  body: unknown;
  status: number;
  statusText: string;
  headers: Headers;
  ok: boolean;

  constructor(body?: unknown, init?: ResponseInitLike) {
    this.body = body;
    this.status = init?.status ?? 200;
    this.statusText = init?.statusText ?? "";
    this.headers = new Headers(init?.headers);
    this.ok = this.status >= 200 && this.status < 300;
  }

  async text(): Promise<string> {
    return typeof this.body === "string" ? this.body : "";
  }

  async json(): Promise<unknown> {
    const raw = await this.text();
    return raw ? JSON.parse(raw) : null;
  }
}

// Polyfill Response if not available
if (typeof Response === 'undefined') {
  (globalThis as unknown as { Response: unknown }).Response = PolyfilledResponse;
}

// Mock fetch globally
const mockFetch = jest.fn(() =>
  Promise.resolve(new PolyfilledResponse(JSON.stringify({ message: 'success' }), { status: 200 }))
);

(globalThis as unknown as { fetch: unknown }).fetch = mockFetch;
