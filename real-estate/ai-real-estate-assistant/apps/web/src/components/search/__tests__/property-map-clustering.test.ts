import { clusterMapPoints } from "../property-map-clustering";

describe("property-map-clustering", () => {
  it("returns points without clustering for small inputs", () => {
    const items = clusterMapPoints(
      [
        { id: "a", lat: 52.23, lon: 21.01 },
        { id: "b", lat: 52.24, lon: 21.02 },
      ],
      12
    );

    expect(items).toHaveLength(2);
    expect(items.every((i) => i.kind === "point")).toBe(true);
  });

  it("clusters dense points into a single cluster", () => {
    const points = Array.from({ length: 80 }, (_, idx) => ({
      id: `p-${idx}`,
      lat: 52.23,
      lon: 21.01,
      title: `P${idx}`,
    }));

    const items = clusterMapPoints(points, 12);

    expect(items).toHaveLength(1);
    expect(items[0].kind).toBe("cluster");
    if (items[0].kind === "cluster") {
      expect(items[0].count).toBe(80);
      expect(items[0].id).toMatch(/^cluster-\d+-\d+$/);
      expect(items[0].lat).toBeCloseTo(52.23, 6);
      expect(items[0].lon).toBeCloseTo(21.01, 6);
    }
  });

  it("does not cluster when zoom is high", () => {
    const points = Array.from({ length: 80 }, (_, idx) => ({
      id: `p-${idx}`,
      lat: 52.23,
      lon: 21.01,
    }));

    const items = clusterMapPoints(points, 18);
    expect(items).toHaveLength(80);
    expect(items.every((i) => i.kind === "point")).toBe(true);
  });

  it("splits distant dense points into multiple clusters", () => {
    const groupA = Array.from({ length: 40 }, (_, idx) => ({ id: `a-${idx}`, lat: 52.23, lon: 21.01 }));
    const groupB = Array.from({ length: 40 }, (_, idx) => ({ id: `b-${idx}`, lat: 48.8566, lon: 2.3522 }));
    const points = [...groupA, ...groupB];

    const items = clusterMapPoints(points, 12);

    const counts = items.map((i) => (i.kind === "cluster" ? i.count : 1));
    expect(counts.reduce((acc, v) => acc + v, 0)).toBe(80);
    expect(items.some((i) => i.kind === "cluster")).toBe(true);
  });
});
