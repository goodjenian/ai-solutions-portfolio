import { computeBounds, computeCenter, extractMapPoints } from "../property-map-utils";
import type { Property, SearchResultItem } from "@/lib/types";

function makeProperty(overrides: Partial<Property>): Property {
  return {
    city: "Warsaw",
    property_type: "apartment",
    listing_type: "rent",
    has_parking: false,
    has_garden: false,
    has_pool: false,
    has_garage: false,
    has_bike_room: false,
    ...overrides,
  };
}

describe("property-map-utils", () => {
  it("extracts only results with numeric latitude/longitude", () => {
    const results: SearchResultItem[] = [
      {
        property: makeProperty({ id: "a", country: "PL", latitude: 52.2297, longitude: 21.0122 }),
        score: 0.9,
      },
      {
        property: makeProperty({ id: "b", country: "PL" }),
        score: 0.8,
      },
      {
        property: makeProperty({ id: "c", country: "PL", latitude: "52.2" as unknown as number, longitude: 21.0 }),
        score: 0.7,
      },
    ];

    const points = extractMapPoints(results);
    expect(points).toHaveLength(1);
    expect(points[0]).toMatchObject({ id: "a", lat: 52.2297, lon: 21.0122, city: "Warsaw", country: "PL" });
  });

  it("computes bounds for multiple points", () => {
    const bounds = computeBounds([
      { id: "a", lat: 1, lon: 10 },
      { id: "b", lat: 2, lon: 20 },
      { id: "c", lat: -3, lon: 15 },
    ]);
    expect(bounds).toEqual([
      [-3, 10],
      [2, 20],
    ]);
  });

  it("returns null bounds for empty points", () => {
    expect(computeBounds([])).toBeNull();
  });

  it("computes center as average", () => {
    const center = computeCenter([
      { id: "a", lat: 0, lon: 0 },
      { id: "b", lat: 2, lon: 4 },
    ]);
    expect(center).toEqual({ lat: 1, lon: 2 });
  });

  it("returns null center for empty points", () => {
    expect(computeCenter([])).toBeNull();
  });
});
