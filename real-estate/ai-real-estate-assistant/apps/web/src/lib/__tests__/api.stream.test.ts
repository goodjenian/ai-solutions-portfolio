import { streamChatMessage, ApiError } from "../api";
import type { ChatRequest } from "../types";

describe("streamChatMessage", () => {
  const g = global as unknown as { fetch: typeof fetch; TextDecoder: typeof TextDecoder };
  const originalFetch = g.fetch;
  const originalTextDecoder = g.TextDecoder;

  beforeEach(() => {
    jest.resetAllMocks();
  });

  afterEach(() => {
    g.fetch = originalFetch;
    g.TextDecoder = originalTextDecoder;
  });

  function createMockReadable(chunks: string[]) {
    const encoded = chunks.map(c => Uint8Array.from(Buffer.from(c, "utf-8")));
    let index = 0;
    return {
      getReader() {
        return {
          async read() {
            if (index < encoded.length) {
              const value = encoded[index++];
              return { done: false, value };
            }
            return { done: true, value: undefined };
          }
        };
      }
    } as unknown as ReadableStream;
  }

  it("parses SSE data chunks and calls onChunk", async () => {
    class FakeTextDecoder {
      decode(u: Uint8Array) {
        return Buffer.from(u).toString("utf-8");
      }
    }
    g.TextDecoder = FakeTextDecoder as unknown as typeof TextDecoder;
    const chunks = [
      "data: {\"content\":\"Hello\"}\n\n",
      "data: {\"content\":\"world\"}\n\n",
      "data: [DONE]\n\n",
    ];
    g.fetch = jest.fn().mockResolvedValue({
      ok: true,
      body: createMockReadable(chunks),
      headers: { get: (name: string) => (name === "X-Request-ID" ? "req-456" : null) },
    }) as unknown as typeof fetch;

    const received: string[] = [];
    let startedWith: string | undefined;

    await streamChatMessage(
      { message: "hi" } as ChatRequest,
      (chunk) => received.push(chunk),
      ({ requestId }) => {
        startedWith = requestId;
      }
    );

    expect(received.join("")).toBe("Helloworld");
    expect(startedWith).toBe("req-456");
  });

  it("parses meta SSE event and calls onMeta with sources", async () => {
    class FakeTextDecoder {
      decode(u: Uint8Array) {
        return Buffer.from(u).toString("utf-8");
      }
    }
    g.TextDecoder = FakeTextDecoder as unknown as typeof TextDecoder;
    const chunks = [
      "data: {\"content\":\"Hello\"}\n\n",
      "event: meta\ndata: {\"sources\":[{\"content\":\"Doc\",\"metadata\":{\"id\":\"1\"}}],\"session_id\":\"sid-1\"}\n\n",
      "data: [DONE]\n\n",
    ];
    g.fetch = jest.fn().mockResolvedValue({
      ok: true,
      body: createMockReadable(chunks),
      headers: { get: () => null },
    }) as unknown as typeof fetch;

    const metas: Array<{ sources?: unknown; sessionId?: unknown }> = [];
    await streamChatMessage(
      { message: "hi" } as ChatRequest,
      () => {},
      undefined,
      (meta) => metas.push(meta)
    );

    expect(metas).toHaveLength(1);
    expect((metas[0] as { sessionId?: string }).sessionId).toBe("sid-1");
    expect(Array.isArray((metas[0] as { sources?: unknown[] }).sources)).toBe(true);
  });

  it("propagates ApiError with request_id if present", async () => {
    const mockResponse = {
      ok: false,
      status: 500,
      text: () => Promise.resolve("Stream error"),
      headers: { get: (name: string) => (name === "X-Request-ID" ? "req-999" : null) },
    };
    g.fetch = jest.fn().mockResolvedValue(mockResponse as unknown as typeof fetch);

    try {
      await streamChatMessage({ message: "x" } as ChatRequest, () => {});
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      if (e instanceof ApiError) {
        expect(e.message).toBe("Stream error");
        expect(e.status).toBe(500);
        expect(e.request_id).toBe("req-999");
      }
    }
  });

  it("throws when the stream yields an error JSON payload", async () => {
    class FakeTextDecoder {
      decode(u: Uint8Array) {
        return Buffer.from(u).toString("utf-8");
      }
    }
    g.TextDecoder = FakeTextDecoder as unknown as typeof TextDecoder;
    const chunks = ["data: {\"error\":\"bad\"}\n\n", "data: [DONE]\n\n"];
    g.fetch = jest.fn().mockResolvedValue({
      ok: true,
      body: createMockReadable(chunks),
      headers: { get: () => null },
    }) as unknown as typeof fetch;

    await expect(streamChatMessage({ message: "x" } as ChatRequest, () => {})).rejects.toThrow("bad");
  });

  it("passes through non-JSON data payloads as chunks", async () => {
    class FakeTextDecoder {
      decode(u: Uint8Array) {
        return Buffer.from(u).toString("utf-8");
      }
    }
    g.TextDecoder = FakeTextDecoder as unknown as typeof TextDecoder;
    const chunks = ["data: hello\n\n", "data: [DONE]\n\n"];
    g.fetch = jest.fn().mockResolvedValue({
      ok: true,
      body: createMockReadable(chunks),
      headers: { get: () => null },
    }) as unknown as typeof fetch;

    const received: string[] = [];
    await streamChatMessage({ message: "x" } as ChatRequest, (chunk) => received.push(chunk));
    expect(received).toEqual(["hello"]);
  });
});
