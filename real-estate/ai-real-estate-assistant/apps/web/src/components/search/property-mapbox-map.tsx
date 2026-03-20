'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import mapboxgl, { type LngLatBoundsLike, type Map as MapboxMap } from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import type { FeatureCollection, GeoJsonProperties, Geometry } from 'geojson';

import {
  computeBounds,
  computeCenter,
  type PropertyMapPoint,
  type HeatmapMode,
} from './property-map-utils';
import { clusterMapPoints, type ClusteredMapItem } from './property-map-clustering';
import HeatmapLegend from './heatmap-legend';
import GeoDrawControl, { type PolygonCoordinates } from './geo-draw-control';
import { generatePopupHTML } from './property-map-popup';

interface MapboxPropertyMapProps {
  points: PropertyMapPoint[];
  mapboxToken?: string;
  showHeatmap?: boolean;
  heatmapIntensity?: number;
  heatmapMode?: HeatmapMode;
  showClusters?: boolean;
  enableDrawing?: boolean;
  onMarkerClick?: (point: PropertyMapPoint) => void;
  onPolygonDraw?: (coordinates: PolygonCoordinates[]) => void;
  onPolygonClear?: () => void;
  className?: string;
  height?: string | number;
  mobileHeight?: string | number;
}

const DEFAULT_CENTER: [number, number] = [21.0122, 52.2297]; // [lon, lat] for Warsaw

// Heatmap color schemes by mode
const HEATMAP_COLORS: Record<HeatmapMode, unknown[]> = {
  density: [
    'interpolate',
    ['linear'],
    ['heatmap-density'],
    0,
    'rgba(33, 102, 172, 0)',
    0.2,
    'rgb(103, 169, 207)',
    0.4,
    'rgb(209, 229, 240)',
    0.6,
    'rgb(253, 219, 199)',
    0.8,
    'rgb(239, 138, 98)',
    1,
    'rgb(178, 24, 43)',
  ],
  price: [
    'interpolate',
    ['linear'],
    ['heatmap-density'],
    0,
    'rgba(34, 197, 94, 0)',
    0.25,
    'rgb(34, 197, 94)',
    0.5,
    'rgb(234, 179, 8)',
    0.75,
    'rgb(249, 115, 22)',
    1,
    'rgb(239, 68, 68)',
  ],
  price_per_sqm: [
    'interpolate',
    ['linear'],
    ['heatmap-density'],
    0,
    'rgba(34, 197, 94, 0)',
    0.25,
    'rgb(34, 197, 94)',
    0.5,
    'rgb(234, 179, 8)',
    0.75,
    'rgb(249, 115, 22)',
    1,
    'rgb(239, 68, 68)',
  ],
  yield: [
    'interpolate',
    ['linear'],
    ['heatmap-density'],
    0,
    'rgba(239, 68, 68, 0)',
    0.25,
    'rgb(239, 68, 68)',
    0.5,
    'rgb(234, 179, 8)',
    0.75,
    'rgb(132, 204, 22)',
    1,
    'rgb(34, 197, 94)',
  ],
};

// Calculate weight based on heatmap mode
function calculateWeight(point: PropertyMapPoint, mode: HeatmapMode): number {
  switch (mode) {
    case 'density':
      // Default: inverse relationship to normalize
      return point.price ? 1 / (point.price / 10000 + 1) : 0.5;
    case 'price':
      if (!point.price) return 0;
      // Normalize to 0-1 range (assuming prices up to 2M)
      return Math.min(point.price / 2000000, 1);
    case 'price_per_sqm':
      if (!point.price_per_sqm) return 0;
      // Normalize to 0-1 range (assuming up to 10000 per sqm)
      return Math.min(point.price_per_sqm / 10000, 1);
    case 'yield':
      // Yield is inverse - higher is better (greener)
      // Assume yield range 2-10%
      if (!point.price || !point.area_sqm) return 0;
      // Estimate yield (rental yield = monthly_rent * 12 / price)
      // Since we don't have rent, use inverse of price_per_sqm as proxy
      const estimatedYield = point.price_per_sqm ? (10000 / point.price_per_sqm) * 0.5 : 0;
      return Math.min(Math.max(estimatedYield / 10, 0), 1);
    default:
      return 0.5;
  }
}

// Calculate min/max values for legend
function getValueRange(
  points: PropertyMapPoint[],
  mode: HeatmapMode
): { min?: number; max?: number } {
  if (mode === 'density' || points.length === 0) return {};

  const values = points
    .map((p) => {
      switch (mode) {
        case 'price':
          return p.price;
        case 'price_per_sqm':
          return p.price_per_sqm;
        case 'yield':
          return p.price_per_sqm ? (10000 / p.price_per_sqm) * 0.5 : undefined;
        default:
          return undefined;
      }
    })
    .filter((v): v is number => v !== undefined);

  if (values.length === 0) return {};

  return {
    min: Math.min(...values),
    max: Math.max(...values),
  };
}

export default function PropertyMapboxMap({
  points,
  mapboxToken,
  showHeatmap = false,
  heatmapIntensity = 1,
  heatmapMode = 'density',
  showClusters = true,
  enableDrawing = false,
  onMarkerClick,
  onPolygonDraw,
  onPolygonClear,
  className = '',
  height = '420px',
  mobileHeight = '60vh',
}: MapboxPropertyMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<MapboxMap | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapInstance, setMapInstance] = useState<MapboxMap | null>(null);
  const [zoom, setZoom] = useState(12);

  const center = useMemo(() => {
    const computed = computeCenter(points);
    return computed ? ([computed.lon, computed.lat] as [number, number]) : DEFAULT_CENTER;
  }, [points]);

  const bounds = useMemo(() => {
    const computed = computeBounds(points);
    if (!computed) return null;
    return [
      [computed[0][1], computed[0][0]],
      [computed[1][1], computed[1][0]],
    ] as LngLatBoundsLike;
  }, [points]);

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    if (!mapboxToken) {
      console.warn('Mapbox token not provided. Using fallback styling.');
    }

    mapboxgl.accessToken = mapboxToken || '';

    const mapInstance = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/streets-v12',
      center,
      zoom: 12,
      scrollZoom: false,
    });

    mapInstance.on('load', () => {
      setMapLoaded(true);
      map.current = mapInstance;
      setMapInstance(mapInstance);

      // Add navigation controls
      mapInstance.addControl(new mapboxgl.NavigationControl(), 'top-right');
    });

    mapInstance.on('zoom', () => {
      setZoom(mapInstance.getZoom());
    });

    mapInstance.on('moveend', () => {
      setZoom(mapInstance.getZoom());
    });

    return () => {
      mapInstance.remove();
      map.current = null;
    };
  }, [mapboxToken, center]);

  // Fit bounds when points change
  useEffect(() => {
    if (!map.current || !bounds || !mapLoaded) return;
    map.current.fitBounds(bounds, { padding: 50, maxZoom: 15 });
  }, [bounds, mapLoaded]);

  // Update markers and heatmap when points or zoom changes
  useEffect(() => {
    if (!map.current || !mapLoaded) return;

    const mapInstance = map.current;

    // Remove existing sources and layers
    const existingSources = ['markers', 'heatmap', 'clusters'];
    existingSources.forEach((sourceId) => {
      if (mapInstance.getSource(sourceId)) {
        mapInstance.removeLayer(sourceId);
        mapInstance.removeSource(sourceId);
      }
    });

    // Remove existing markers
    const markers = document.querySelectorAll('.mapboxgl-marker');
    markers.forEach((marker) => marker.remove());

    if (points.length === 0) return;

    // Add heatmap layer if enabled
    if (showHeatmap && points.length > 1) {
      const heatData: FeatureCollection<Geometry, GeoJsonProperties> = {
        type: 'FeatureCollection',
        features: points.map((point) => ({
          type: 'Feature',
          geometry: {
            type: 'Point',
            coordinates: [point.lon, point.lat],
          },
          properties: {
            weight: calculateWeight(point, heatmapMode),
          },
        })),
      };

      mapInstance.addSource('heatmap', {
        type: 'geojson',
        data: heatData,
      });

      mapInstance.addLayer({
        id: 'heatmap',
        type: 'heatmap',
        source: 'heatmap',
        paint: {
          'heatmap-weight': ['get', 'weight'],
          'heatmap-intensity': heatmapIntensity,
          'heatmap-radius': Math.max(10, 30 - zoom),
          'heatmap-opacity': 0.7,
          // eslint-disable-next-line @typescript-eslint/no-explicit-any -- mapbox-gl heatmap-color requires expression type not covered by types
          'heatmap-color': HEATMAP_COLORS[heatmapMode] as any,
        },
      });
    }

    // Add markers
    const items = showClusters
      ? clusterMapPoints(points, zoom)
      : points.map((point) => ({ kind: 'point', point }));

    items.forEach((item) => {
      if (item.kind === 'point') {
        const p = item.point;
        const el = document.createElement('div');
        el.className = 'cursor-pointer';
        el.innerHTML = `<div style="width:14px;height:14px;background:#2563eb;border-radius:9999px;border:2px solid white;box-shadow:0 1px 2px rgba(0,0,0,0.3)"></div>`;
        el.addEventListener('click', () => onMarkerClick?.(p));

        new mapboxgl.Marker({ element: el })
          .setLngLat([p.lon, p.lat])
          .setPopup(
            new mapboxgl.Popup({ offset: 15, maxWidth: '280px' }).setHTML(generatePopupHTML(p))
          )
          .addTo(mapInstance);
      } else {
        // Cluster
        const cluster = item as Extract<ClusteredMapItem, { kind: 'cluster' }>;
        const el = document.createElement('div');
        el.className = 'cursor-pointer';
        el.innerHTML = `<div style="min-width:30px;height:30px;padding:0 8px;background:#1d4ed8;color:white;border-radius:9999px;border:2px solid white;box-shadow:0 1px 2px rgba(0,0,0,0.35);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;line-height:1">${cluster.count}</div>`;
        el.addEventListener('click', () => {
          const clusterBounds = computeBounds(cluster.points);
          if (clusterBounds) {
            mapInstance.fitBounds(
              [
                [clusterBounds[0][1], clusterBounds[0][0]],
                [clusterBounds[1][1], clusterBounds[1][0]],
              ],
              { padding: 50, maxZoom: Math.min(zoom + 2, 18) }
            );
          }
        });

        // Calculate cluster stats
        const prices = cluster.points
          .map((p) => p.price)
          .filter((p): p is number => p !== undefined);
        const minPrice = prices.length > 0 ? Math.min(...prices) : null;
        const maxPrice = prices.length > 0 ? Math.max(...prices) : null;
        const avgPrice =
          prices.length > 0 ? Math.round(prices.reduce((a, b) => a + b, 0) / prices.length) : null;

        const formatClusterPrice = (price: number): string => {
          if (price >= 1000000) return `$${(price / 1000000).toFixed(1)}M`;
          return `$${(price / 1000).toFixed(0)}K`;
        };

        const clusterPopupHTML = `
          <div style="min-width:180px;font-family:system-ui,-apple-system,sans-serif;">
            <div style="font-weight:600;font-size:14px;margin-bottom:8px;">
              ${cluster.count} properties in this area
            </div>
            ${
              minPrice !== null && maxPrice !== null
                ? `
              <div style="font-size:12px;color:#6b7280;margin-bottom:4px;">
                Price range: ${formatClusterPrice(minPrice)} - ${formatClusterPrice(maxPrice)}
              </div>
            `
                : ''
            }
            ${
              avgPrice !== null
                ? `
              <div style="font-size:12px;color:#6b7280;margin-bottom:8px;">
                Average: ${formatClusterPrice(avgPrice)}
              </div>
            `
                : ''
            }
            <div style="font-size:11px;color:#9ca3af;">
              Click to zoom in
            </div>
          </div>
        `;

        new mapboxgl.Marker({ element: el })
          .setLngLat([cluster.lon, cluster.lat])
          .setPopup(new mapboxgl.Popup({ offset: 15 }).setHTML(clusterPopupHTML))
          .addTo(mapInstance);
      }
    });
  }, [
    points,
    zoom,
    mapLoaded,
    showHeatmap,
    heatmapIntensity,
    heatmapMode,
    showClusters,
    onMarkerClick,
  ]);

  // Calculate value range for legend
  const valueRange = useMemo(() => getValueRange(points, heatmapMode), [points, heatmapMode]);

  // Detect if mobile viewport
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;

  // Calculate responsive height
  const mapHeight = isMobile ? mobileHeight : height;

  return (
    <div
      className={`rounded-lg border bg-card text-card-foreground shadow-sm overflow-hidden relative ${className}`}
    >
      <div
        ref={mapContainer}
        className="w-full"
        style={{ height: mapHeight }}
        aria-label="Property map with Mapbox"
      />
      {!mapboxToken && (
        <div className="absolute inset-0 flex items-center justify-center bg-muted/50">
          <p className="text-sm text-muted-foreground">
            Mapbox token not configured. Add NEXT_PUBLIC_MAPBOX_TOKEN to your environment.
          </p>
        </div>
      )}
      {/* Polygon drawing control */}
      {mapLoaded && mapInstance && (
        <GeoDrawControl
          map={mapInstance}
          enabled={enableDrawing}
          onPolygonComplete={onPolygonDraw}
          onDrawDelete={onPolygonClear}
        />
      )}
      {/* Heatmap legend */}
      {showHeatmap && mapLoaded && (
        <HeatmapLegend
          mode={heatmapMode}
          minValue={valueRange.min}
          maxValue={valueRange.max}
          className="absolute bottom-4 right-4 z-10"
        />
      )}
      {/* Drawing mode indicator */}
      {enableDrawing && mapLoaded && (
        <div className="absolute top-4 left-4 z-10 bg-background/95 backdrop-blur-sm rounded-lg border shadow-sm px-3 py-2 text-xs text-muted-foreground">
          Draw a polygon to filter properties
        </div>
      )}
      {/* Mobile swipe indicator */}
      {isMobile && (
        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 z-10 bg-background/95 backdrop-blur-sm rounded-full border shadow-sm px-3 py-1 text-xs text-muted-foreground">
          Swipe up for list
        </div>
      )}
    </div>
  );
}
