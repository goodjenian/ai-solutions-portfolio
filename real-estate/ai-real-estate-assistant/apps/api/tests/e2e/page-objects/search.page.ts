/**
 * Search Page Object for E2E tests.
 * Encapsulates search page interactions and elements.
 */

import { Page, Locator, expect } from '@playwright/test';

export class SearchPage {
  readonly page: Page;
  readonly searchInput: Locator;
  readonly searchButton: Locator;
  readonly resultsContainer: Locator;
  readonly mapContainer: Locator;
  readonly listContainer: Locator;
  readonly resultCount: Locator;
  readonly noResultsMessage: Locator;
  readonly loadingSpinner: Locator;
  readonly filtersPanel: Locator;
  readonly mapViewButton: Locator;
  readonly listViewButton: Locator;
  readonly exportButton: Locator;

  constructor(page: Page) {
    this.page = page;
    // Actual UI: input with aria-label="Search query" inside form with role="search"
    this.searchInput = page.getByLabel('Search query').or(page.getByPlaceholder(/describe what you.re looking for/i));
    this.searchButton = page.getByRole('button', { name: /^search$/i }).or(page.locator('form[role="search"] button[type="submit"]'));
    // Results are displayed in a grid with property cards
    this.resultsContainer = page.locator('.grid.grid-cols-1.md\\:grid-cols-2').or(page.locator('article, .rounded-lg.border.bg-card'));
    this.mapContainer = page.locator('.h-\\[420px\\]').or(page.locator('[class*="map"]'));
    this.listContainer = page.locator('.grid.grid-cols-1');
    this.resultCount = page.locator('text=/\\d+.*shown/i');
    this.noResultsMessage = page.locator('text=/no results found/i');
    this.loadingSpinner = page.locator('.animate-pulse');
    this.filtersPanel = page.locator('.rounded-lg.border.bg-card.text-card-foreground.shadow-sm.p-6').first();
    this.mapViewButton = page.getByRole('button', { name: /^map$/i });
    this.listViewButton = page.getByRole('button', { name: /^list$/i });
    this.exportButton = page.getByRole('button', { name: /export$/i });
  }

  /**
   * Navigate to the search page.
   */
  async navigate(): Promise<void> {
    await this.page.goto('/search');
    // Wait for the search input to be visible
    await expect(this.searchInput).toBeVisible({ timeout: 10000 });
  }

  /**
   * Perform a search query.
   */
  async search(query: string): Promise<void> {
    await this.searchInput.fill(query);
    await this.searchButton.click();
    // Wait for loading to complete
    await this.waitForResults();
  }

  /**
   * Wait for search results to load.
   */
  async waitForResults(): Promise<void> {
    // Wait for either results or no-results message
    await Promise.race([
      expect(this.resultsContainer).toBeVisible({ timeout: 15000 }),
      expect(this.noResultsMessage).toBeVisible({ timeout: 15000 }),
    ]);
  }

  /**
   * Get the number of results displayed.
   */
  async getResultCount(): Promise<number> {
    const text = await this.resultCount.textContent();
    if (!text) return 0;
    // Parse "X results" or "Found X properties"
    const match = text.match(/(\d+)/);
    return match ? parseInt(match[1], 10) : 0;
  }

  /**
   * Get all property card elements.
   */
  async getPropertyCards(): Promise<Locator[]> {
    await this.waitForResults();
    const cards = this.resultsContainer.locator('[data-testid="property-card"], .property-card, article');
    return await cards.all();
  }

  /**
   * Click on a property card by index.
   */
  async clickPropertyCard(index: number = 0): Promise<void> {
    const cards = await this.getPropertyCards();
    if (cards[index]) {
      await cards[index].click();
    } else {
      throw new Error(`Property card at index ${index} not found`);
    }
  }

  /**
   * Toggle to map view.
   */
  async switchToMapView(): Promise<void> {
    await this.mapViewButton.click();
    await expect(this.mapContainer).toBeVisible({ timeout: 5000 });
  }

  /**
   * Toggle to list view.
   */
  async switchToListView(): Promise<void> {
    await this.listViewButton.click();
    await expect(this.listContainer).toBeVisible({ timeout: 5000 });
  }

  /**
   * Set price range filter.
   */
  async setPriceRange(min: number, max: number): Promise<void> {
    const minInput = this.filtersPanel.getByRole('spinbutton', { name: /min/i });
    const maxInput = this.filtersPanel.getByRole('spinbutton', { name: /max/i });

    if (await minInput.isVisible()) {
      await minInput.fill(min.toString());
    }
    if (await maxInput.isVisible()) {
      await maxInput.fill(max.toString());
    }
  }

  /**
   * Set minimum rooms filter.
   */
  async setMinRooms(rooms: number): Promise<void> {
    const roomsInput = this.filtersPanel.getByRole('spinbutton', { name: /rooms|bedrooms/i });
    if (await roomsInput.isVisible()) {
      await roomsInput.fill(rooms.toString());
    }
  }

  /**
   * Apply filters (click apply button if exists).
   */
  async applyFilters(): Promise<void> {
    const applyButton = this.filtersPanel.getByRole('button', { name: /apply|filter/i });
    if (await applyButton.isVisible()) {
      await applyButton.click();
      await this.waitForResults();
    }
  }

  /**
   * Check if no results message is displayed.
   */
  async hasNoResults(): Promise<boolean> {
    return await this.noResultsMessage.isVisible();
  }

  /**
   * Check if results are displayed.
   */
  async hasResults(): Promise<boolean> {
    return await this.resultsContainer.isVisible();
  }

  /**
   * Export results in the specified format.
   */
  async exportResults(format: 'csv' | 'excel' | 'json' = 'csv'): Promise<void> {
    await this.exportButton.click();

    // Select format if dropdown appears
    const formatOption = this.page.getByRole('option', { name: format });
    if (await formatOption.isVisible({ timeout: 2000 }).catch(() => false)) {
      await formatOption.click();
    }

    // Confirm export
    const confirmButton = this.page.getByRole('button', { name: /export|download|confirm/i });
    if (await confirmButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await confirmButton.click();
    }
  }
}
