export type ChatSource = {
  content: string;
  metadata: Record<string, unknown>;
};

function toDisplayString(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (value instanceof Date) return value.toISOString();
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function basenameFromPath(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) return "";
  const normalized = trimmed.replace(/\\/g, "/");
  const parts = normalized.split("/").filter(Boolean);
  return parts.length ? parts[parts.length - 1] : trimmed;
}

function extractFromUrl(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) return "";
  try {
    const url = new URL(trimmed);
    const name = basenameFromPath(url.pathname);
    return name || url.host || trimmed;
  } catch {
    return basenameFromPath(trimmed);
  }
}

export function extractSourceTitle(metadata: Record<string, unknown>): string | null {
  const candidates: Array<{ key: string; kind: "path" | "url" | "raw" }> = [
    { key: "title", kind: "raw" },
    { key: "source", kind: "raw" },
    { key: "file_name", kind: "path" },
    { key: "filename", kind: "path" },
    { key: "path", kind: "path" },
    { key: "url", kind: "url" },
  ];

  for (const { key, kind } of candidates) {
    const raw = metadata[key];
    if (raw === undefined || raw === null) continue;
    const asString = toDisplayString(raw).trim();
    if (!asString) continue;
    if (kind === "path") return basenameFromPath(asString) || asString;
    if (kind === "url") return extractFromUrl(asString) || asString;
    return asString;
  }

  const id = metadata.id;
  if (id !== undefined && id !== null) {
    const idStr = toDisplayString(id).trim();
    return idStr ? `id:${idStr}` : null;
  }

  return null;
}

export function truncateText(text: string, maxChars: number): string {
  const safeMax = Math.max(0, Math.floor(maxChars));
  if (!safeMax) return "";
  if (text.length <= safeMax) return text;
  const slice = text.slice(0, safeMax);
  return `${slice}…`;
}

export function formatMetadataInline(metadata: Record<string, unknown>, maxPairs = 6): string {
  const safeMax = Math.max(0, Math.floor(maxPairs));
  if (!safeMax) return "";

  const priorityKeys = [
    "title",
    "source",
    "file_name",
    "filename",
    "path",
    "url",
    "id",
    "page",
    "chunk_index",
    "chunk",
  ];

  const entries: Array<[string, unknown]> = [];
  const seen = new Set<string>();
  for (const key of priorityKeys) {
    if (Object.prototype.hasOwnProperty.call(metadata, key)) {
      entries.push([key, metadata[key]]);
      seen.add(key);
    }
  }

  const otherKeys = Object.keys(metadata)
    .filter(k => !seen.has(k))
    .sort((a, b) => a.localeCompare(b));
  for (const key of otherKeys) {
    entries.push([key, metadata[key]]);
  }

  const parts: string[] = [];
  for (const [key, value] of entries) {
    if (parts.length >= safeMax) break;
    const rendered = toDisplayString(value).trim();
    if (!rendered) continue;
    const safeValue = truncateText(rendered, 120);
    parts.push(`${key}=${safeValue}`);
  }

  return parts.join(" · ");
}
