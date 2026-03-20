/**
 * Register Page Object for E2E tests.
 * Encapsulates registration page interactions and elements.
 */

import { Page, Locator, expect } from '@playwright/test';

export class RegisterPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly fullNameInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;
  readonly successMessage: Locator;
  readonly loginLink: Locator;

  constructor(page: Page) {
    this.page = page;
    // Actual UI: inputs with labels "Email", "Password", "Full Name"
    this.emailInput = page.getByLabel('Email').or(page.getByRole('textbox', { name: /email/i }));
    this.passwordInput = page.getByLabel('Password').or(page.getByRole('textbox', { name: /^password$/i }));
    // Note: No confirm password field in actual UI
    this.fullNameInput = page.getByLabel('Full Name').or(page.getByRole('textbox', { name: /full name|name/i }));
    // Submit button text is "Create Account" - must be inside form to avoid matching nav buttons
    this.submitButton = page.locator('form button[type="submit"]').or(
      page.locator('button[type="submit"]').filter({ hasText: /create account|sign up|register|zarejestruj/i })
    );
    // Error message is in a div with bg-destructive/15 class - be specific to avoid matching Next.js route announcer
    this.errorMessage = page.locator('.bg-destructive\\/15, .text-destructive').filter({ has: page.locator('svg, span, p') }).first();
    this.successMessage = page.locator('[data-testid="success-message"], .success-message');
    this.loginLink = page.getByRole('link', { name: /sign in/i });
  }

  /**
   * Navigate to the registration page.
   */
  async navigate(): Promise<void> {
    await this.page.goto('/auth/register');
    // Wait for the form to be visible
    await expect(this.emailInput).toBeVisible({ timeout: 10000 });
  }

  /**
   * Fill the registration form.
   */
  async fillForm(options: {
    email: string;
    password: string;
    fullName?: string;
    confirmPassword?: string; // Kept for API compatibility but ignored (no confirm field in UI)
  }): Promise<void> {
    await this.emailInput.fill(options.email);
    await this.passwordInput.fill(options.password);

    if (options.fullName) {
      await this.fullNameInput.fill(options.fullName);
    }
    // Note: confirmPassword is ignored - actual UI doesn't have this field
  }

  /**
   * Submit the registration form.
   */
  async submit(): Promise<void> {
    await this.submitButton.click();
  }

  /**
   * Perform a complete registration action.
   */
  async register(options: {
    email: string;
    password: string;
    fullName?: string;
    confirmPassword?: string;
  }): Promise<void> {
    await this.fillForm(options);
    await this.submit();
  }

  /**
   * Wait for registration to complete.
   */
  async waitForRegistrationSuccess(): Promise<void> {
    // Wait for success message or redirect
    await Promise.race([
      expect(this.successMessage).toBeVisible({ timeout: 10000 }),
      this.page.waitForURL(/^(?!.*\/auth\/register).*$/, { timeout: 10000 }),
    ]);
  }

  /**
   * Wait for error message to appear.
   */
  async waitForError(): Promise<string> {
    await expect(this.errorMessage).toBeVisible({ timeout: 5000 });
    return (await this.errorMessage.textContent()) || '';
  }

  /**
   * Check if error message is visible.
   */
  async hasError(): Promise<boolean> {
    return await this.errorMessage.isVisible();
  }

  /**
   * Click the login link.
   */
  async clickLogin(): Promise<void> {
    await this.loginLink.click();
  }
}
