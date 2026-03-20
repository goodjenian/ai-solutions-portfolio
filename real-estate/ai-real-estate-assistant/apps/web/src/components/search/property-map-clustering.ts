import { type PropertyMapPoint } from "./property-map-utils";

export type ClusteredMapItem =
  | { kind: "point"; point: PropertyMapPoint }
  | { kind: "cluster"; id: string; lat: number; lon: number; count: number; points: PropertyMapPoint[] };

export type ClusterOptions = {
  cellSizePx?: number;
  maxPointsWithoutClustering?: number;
  maxZoomForClustering?: number;
};

const TILE_SIZE_PX = 256;

function toRad(value: number): number {
  return (value * Math.PI) / 180;
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function latLonToWorldPx(
  lat: number,
  lon: number,
  zoom: number
): {
  x: number;
  y: number;
} {
  const scale = TILE_SIZE_PX * Math.pow(2, zoom);
  const x = ((lon + 180) / 360) * scale;
  const sinLat = Math.sin(toRad(clamp(lat, -85.05112878, 85.05112878)));
  const y = (0.5 - Math.log((1 + sinLat) / (1 - sinLat)) / (4 * Math.PI)) * scale;
  return { x, y };
}

export function clusterMapPoints(points: PropertyMapPoint[], zoom: number, options: ClusterOptions = {}): ClusteredMapItem[] {
  const cellSizePx = options.cellSizePx ?? 60;
  const maxPointsWithoutClustering = options.maxPointsWithoutClustering ?? 75;
  const maxZoomForClustering = options.maxZoomForClustering ?? 15;

  if (points.length <= maxPointsWithoutClustering || zoom >= maxZoomForClustering) {
    return points.map((point) => ({ kind: "point", point }));
  }

  const groups = new Map<
    string,
    {
      cellX: number;
      cellY: number;
      points: PropertyMapPoint[];
      sumLat: number;
      sumLon: number;
    }
  >();

  for (const point of points) {
    const { x, y } = latLonToWorldPx(point.lat, point.lon, zoom);
    const cellX = Math.floor(x / cellSizePx);
    const cellY = Math.floor(y / cellSizePx);
    const key = `${cellX}:${cellY}`;

    const existing = groups.get(key);
    if (!existing) {
      groups.set(key, { cellX, cellY, points: [point], sumLat: point.lat, sumLon: point.lon });
      continue;
    }

    existing.points.push(point);
    existing.sumLat += point.lat;
    existing.sumLon += point.lon;
  }

  return Array.from(groups.values())
    .sort((a, b) => {
      if (a.cellY !== b.cellY) return a.cellY - b.cellY;
      return a.cellX - b.cellX;
    })
    .reduce<ClusteredMapItem[]>((acc, group) => {
      if (group.points.length === 1) {
        acc.push({ kind: "point", point: group.points[0] });
        return acc;
      }

      const count = group.points.length;
      const lat = group.sumLat / count;
      const lon = group.sumLon / count;

      acc.push({
        kind: "cluster",
        id: `cluster-${group.cellX}-${group.cellY}`,
        lat,
        lon,
        count,
        points: group.points,
      });
      return acc;
    }, []);
}
