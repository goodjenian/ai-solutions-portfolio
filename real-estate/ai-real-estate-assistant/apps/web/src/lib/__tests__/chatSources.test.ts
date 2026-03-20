import { extractSourceTitle, formatMetadataInline, truncateText } from "../chatSources";

describe("chatSources", () => {
  describe("truncateText", () => {
    it("returns empty string when maxChars is zero", () => {
      expect(truncateText("hello", 0)).toBe("");
    });

    it("returns the input when shorter than maxChars", () => {
      expect(truncateText("hello", 10)).toBe("hello");
    });

    it("adds ellipsis when truncating", () => {
      expect(truncateText("hello world", 5)).toBe("hello…");
    });
  });

  describe("extractSourceTitle", () => {
    it("prefers title field when present", () => {
      expect(extractSourceTitle({ title: "My Doc", id: "1" })).toBe("My Doc");
    });

    it("extracts basename from Windows-like path", () => {
      expect(extractSourceTitle({ path: "C:\\docs\\report.pdf" })).toBe("report.pdf");
    });

    it("extracts basename from URL", () => {
      expect(extractSourceTitle({ url: "https://example.com/files/doc.txt?x=1" })).toBe("doc.txt");
    });

    it("falls back to id when nothing else is present", () => {
      expect(extractSourceTitle({ id: 123 })).toBe("id:123");
    });
  });

  describe("formatMetadataInline", () => {
    it("formats prioritized keys first and limits pairs", () => {
      const meta = {
        id: "1",
        source: "file.pdf",
        chunk_index: 2,
        extra: "x",
      };
      const rendered = formatMetadataInline(meta, 2);
      expect(rendered).toContain("source=file.pdf");
      expect(rendered).toContain("id=1");
      expect(rendered).not.toContain("chunk_index=");
    });

    it("returns empty string when maxPairs is zero", () => {
      expect(formatMetadataInline({ id: "1" }, 0)).toBe("");
    });
  });
});
