/**
 * Test property fixtures for E2E tests.
 * Provides sample property data for search and display tests.
 */

export interface TestProperty {
  id: string;
  title: string;
  price: number;
  rooms: number;
  area: number;
  city: string;
  neighborhood: string;
  propertyType: 'apartment' | 'house' | 'studio';
  description: string;
}

/**
 * Sample properties for search tests.
 */
export const TEST_PROPERTIES: TestProperty[] = [
  {
    id: 'prop-001',
    title: 'Modern 2-Bedroom Apartment in Mitte',
    price: 1200,
    rooms: 2,
    area: 75,
    city: 'Berlin',
    neighborhood: 'Mitte',
    propertyType: 'apartment',
    description: 'A modern apartment in the heart of Berlin with excellent transport links.',
  },
  {
    id: 'prop-002',
    title: 'Spacious 3-Bedroom Flat in Prenzlauer Berg',
    price: 1500,
    rooms: 3,
    area: 95,
    city: 'Berlin',
    neighborhood: 'Prenzlauer Berg',
    propertyType: 'apartment',
    description: 'Family-friendly apartment near parks and schools.',
  },
  {
    id: 'prop-003',
    title: 'Cozy Studio in Kreuzberg',
    price: 800,
    rooms: 1,
    area: 35,
    city: 'Berlin',
    neighborhood: 'Kreuzberg',
    propertyType: 'studio',
    description: 'Compact studio perfect for young professionals.',
  },
  {
    id: 'prop-004',
    title: 'Family House in Charlottenburg',
    price: 2500,
    rooms: 4,
    area: 150,
    city: 'Berlin',
    neighborhood: 'Charlottenburg',
    propertyType: 'house',
    description: 'Spacious house with garden in a quiet neighborhood.',
  },
  {
    id: 'prop-005',
    title: 'Luxury Penthouse in Friedrichshain',
    price: 3500,
    rooms: 3,
    area: 120,
    city: 'Berlin',
    neighborhood: 'Friedrichshain',
    propertyType: 'apartment',
    description: 'Stunning penthouse with rooftop terrace and city views.',
  },
];

/**
 * Get all test properties.
 */
export function getTestProperties(): TestProperty[] {
  return TEST_PROPERTIES;
}

/**
 * Get a test property by ID.
 */
export function getTestPropertyById(id: string): TestProperty | undefined {
  return TEST_PROPERTIES.find((p) => p.id === id);
}

/**
 * Filter properties by criteria.
 */
export function filterProperties(
  criteria: Partial<{
    minPrice: number;
    maxPrice: number;
    minRooms: number;
    propertyType: string;
    city: string;
  }>
): TestProperty[] {
  return TEST_PROPERTIES.filter((p) => {
    if (criteria.minPrice !== undefined && p.price < criteria.minPrice) return false;
    if (criteria.maxPrice !== undefined && p.price > criteria.maxPrice) return false;
    if (criteria.minRooms !== undefined && p.rooms < criteria.minRooms) return false;
    if (criteria.propertyType !== undefined && p.propertyType !== criteria.propertyType)
      return false;
    if (criteria.city !== undefined && p.city !== criteria.city) return false;
    return true;
  });
}
