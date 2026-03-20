/**
 * Documents Page Object for E2E tests.
 * Encapsulates document management page interactions and elements.
 */

import { Page, Locator, expect } from '@playwright/test';

export class DocumentsPage {
  readonly page: Page;
  readonly header: Locator;
  readonly uploadButton: Locator;
  readonly refreshButton: Locator;
  readonly documentList: Locator;
  readonly emptyState: Locator;
  readonly errorMessage: Locator;
  readonly loadingSpinner: Locator;
  readonly uploadModal: Locator;
  readonly expiringAlert: Locator;
  readonly loadMoreButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.header = page.getByRole('heading', { name: 'Documents' });
    this.uploadButton = page.getByRole('button', { name: /upload document/i });
    this.refreshButton = page.getByRole('button', { name: /refresh/i });
    this.documentList = page.locator('[data-testid="document-list"], .document-list, article').filter({ has: page.locator('[class*="document"]') });
    this.emptyState = page.locator('text=/no documents yet/i');
    this.errorMessage = page.locator('.bg-destructive\\/15, .text-destructive, [role="alert"]').filter({ hasText: /failed/i });
    this.loadingSpinner = page.locator('.animate-spin');
    this.uploadModal = page.locator('.fixed.inset-0.z-50');
    this.expiringAlert = page.locator('.bg-yellow-50, [class*="expiring"]');
    this.loadMoreButton = page.getByRole('button', { name: /load more/i });
  }

  /**
   * Navigate to the documents page.
   */
  async navigate(): Promise<void> {
    await this.page.goto('/documents');
    // Wait for either loading to complete or empty state
    await Promise.race([
      expect(this.loadingSpinner).toBeVisible({ timeout: 5000 }).catch(() => {}),
      expect(this.header).toBeVisible({ timeout: 10000 }),
    ]);
  }

  /**
   * Click the upload button to open the upload modal.
   */
  async openUploadModal(): Promise<void> {
    await this.uploadButton.click();
    await expect(this.uploadModal).toBeVisible({ timeout: 5000 });
  }

  /**
   * Close the upload modal.
   */
  async closeUploadModal(): Promise<void> {
    const closeButton = this.uploadModal.getByRole('button', { name: /×/i }).or(
      this.uploadModal.locator('button').filter({ hasText: '×' })
    );
    await closeButton.click();
    await expect(this.uploadModal).not.toBeVisible({ timeout: 3000 });
  }

  /**
   * Upload a file via the file input.
   */
  async uploadFile(filePath: string): Promise<void> {
    await this.openUploadModal();

    const fileInput = this.uploadModal.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);

    // Wait for upload to complete
    await expect(this.uploadModal).not.toBeVisible({ timeout: 30000 });
  }

  /**
   * Get all document card elements.
   */
  async getDocumentCards(): Promise<Locator[]> {
    const cards = this.page.locator('[data-testid="document-card"], article, .document-card');
    return await cards.all();
  }

  /**
   * Get document count.
   */
  async getDocumentCount(): Promise<number> {
    const cards = await this.getDocumentCards();
    return cards.length;
  }

  /**
   * Click on a document card by index.
   */
  async clickDocumentCard(index: number = 0): Promise<void> {
    const cards = await this.getDocumentCards();
    if (cards[index]) {
      await cards[index].click();
    } else {
      throw new Error(`Document card at index ${index} not found`);
    }
  }

  /**
   * Delete a document by clicking its delete button.
   */
  async deleteDocument(index: number = 0): Promise<void> {
    const cards = await this.getDocumentCards();
    if (cards[index]) {
      const deleteButton = cards[index].getByRole('button', { name: /delete/i });
      await deleteButton.click();

      // Confirm deletion if confirmation dialog appears
      const confirmButton = this.page.getByRole('button', { name: /confirm|yes|delete/i }).filter({ hasText: /delete/i });
      if (await confirmButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await confirmButton.click();
      }
    }
  }

  /**
   * Refresh the document list.
   */
  async refresh(): Promise<void> {
    await this.refreshButton.click();
    // Wait for loading to complete
    await expect(this.loadingSpinner).not.toBeVisible({ timeout: 10000 }).catch(() => {});
  }

  /**
   * Check if expiring documents alert is visible.
   */
  async hasExpiringDocuments(): Promise<boolean> {
    return await this.expiringAlert.isVisible();
  }

  /**
   * Get expiring document names.
   */
  async getExpiringDocumentNames(): Promise<string[]> {
    const text = await this.expiringAlert.textContent();
    if (!text) return [];
    // Extract document names from the alert text
    return text.split(',').map(s => s.trim()).filter(s => s.length > 0);
  }

  /**
   * Check if empty state is displayed.
   */
  async isEmpty(): Promise<boolean> {
    return await this.emptyState.isVisible();
  }

  /**
   * Check if error is displayed.
   */
  async hasError(): Promise<boolean> {
    return await this.errorMessage.isVisible();
  }

  /**
   * Get error message text.
   */
  async getErrorMessage(): Promise<string> {
    return (await this.errorMessage.textContent()) || '';
  }

  /**
   * Load more documents.
   */
  async loadMore(): Promise<void> {
    await this.loadMoreButton.click();
    await expect(this.loadingSpinner).not.toBeVisible({ timeout: 10000 });
  }

  /**
   * Check if load more button is visible.
   */
  async canLoadMore(): Promise<boolean> {
    return await this.loadMoreButton.isVisible();
  }
}
