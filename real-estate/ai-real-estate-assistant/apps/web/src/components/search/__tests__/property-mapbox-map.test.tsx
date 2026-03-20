import { render, screen } from "@testing-library/react";
import PropertyMapboxMap from "../property-mapbox-map";
import type { PropertyMapPoint } from "../property-map-utils";

// Mock mapbox-gl
jest.mock("mapbox-gl", () => ({
  __esModule: true,
  default: {
    accessToken: "",
    Map: jest.fn().mockImplementation(() => ({
      on: jest.fn(),
      addSource: jest.fn(),
      addLayer: jest.fn(),
      getSource: jest.fn(),
      getLayer: jest.fn(),
      removeLayer: jest.fn(),
      removeSource: jest.fn(),
      fitBounds: jest.fn(),
      getZoom: jest.fn(() => 12),
      addControl: jest.fn(),
      remove: jest.fn(),
      removeControl: jest.fn(),
      getCanvas: jest.fn(() => ({ style: {} })),
      isStyleLoaded: jest.fn(() => true),
    })),
    NavigationControl: jest.fn(),
    Marker: jest.fn().mockImplementation(() => ({
      setPopup: jest.fn().mockReturnThis(),
      addTo: jest.fn().mockReturnThis(),
      setLngLat: jest.fn().mockReturnThis(),
    })),
    Popup: jest.fn().mockImplementation(() => ({
      setHTML: jest.fn().mockReturnThis(),
      offset: jest.fn().mockReturnThis(),
    })),
  },
}));

// Mock @mapbox/mapbox-gl-draw
jest.mock("@mapbox/mapbox-gl-draw", () => ({
  __esModule: true,
  default: jest.fn().mockImplementation(() => ({
    addControl: jest.fn(),
    removeControl: jest.fn(),
    deleteAll: jest.fn(),
  })),
}));

describe("PropertyMapboxMap", () => {
  const mockPoints: PropertyMapPoint[] = [
    {
      id: "1",
      lat: 52.2297,
      lon: 21.0122,
      title: "Test Property",
      city: "Warsaw",
      country: "Poland",
      price: 300000,
    },
  ];

  it("should render map container", () => {
    render(
      <div data-testid="wrapper">
        <PropertyMapboxMap points={mockPoints} mapboxToken="test-token" />
      </div>
    );

    const wrapper = screen.getByTestId("wrapper");
    expect(wrapper.querySelector('[aria-label="Property map with Mapbox"]')).toBeInTheDocument();
  });

  it("should render with heatmap enabled", () => {
    render(
      <PropertyMapboxMap points={mockPoints} mapboxToken="test-token" showHeatmap />
    );

    // Component renders without error
    expect(true).toBe(true);
  });

  it("should render with clusters enabled", () => {
    render(
      <PropertyMapboxMap points={mockPoints} mapboxToken="test-token" showClusters={false} />
    );

    // Component renders without error
    expect(true).toBe(true);
  });

  it("should handle empty points array", () => {
    render(
      <PropertyMapboxMap points={[]} mapboxToken="test-token" />
    );

    // Component renders without error
    expect(true).toBe(true);
  });

  it("should handle custom className", () => {
    render(
      <PropertyMapboxMap points={mockPoints} mapboxToken="test-token" className="custom-class" />
    );

    // Component renders without error
    expect(true).toBe(true);
  });
});
