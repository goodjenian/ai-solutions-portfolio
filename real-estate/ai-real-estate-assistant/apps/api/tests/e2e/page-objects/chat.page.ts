/**
 * Chat Page Object for E2E tests.
 * Encapsulates chat page interactions and elements.
 */

import { Page, Locator, expect } from '@playwright/test';

export class ChatPage {
  readonly page: Page;
  readonly messageInput: Locator;
  readonly sendButton: Locator;
  readonly messagesContainer: Locator;
  readonly lastAssistantMessage: Locator;
  readonly retryButton: Locator;
  readonly errorMessage: Locator;
  readonly sourcesContainer: Locator;
  readonly loadingIndicator: Locator;
  readonly suggestedPrompts: Locator;
  readonly sessionHistory: Locator;

  constructor(page: Page) {
    this.page = page;
    // Actual UI: input with aria-label="Chat message input"
    this.messageInput = page.getByLabel(/chat message input/i).or(page.getByPlaceholder(/type your question|ask about properties/i));
    // Send button has aria-label="Send message" or "Sending..."
    this.sendButton = page.getByLabel(/send(ing)? message/i).or(page.locator('form button[type="submit"]'));
    // Messages container - the scrollable div containing messages
    this.messagesContainer = page.locator('.flex-1.overflow-y-auto, .overflow-y-auto').first();
    // Assistant messages - divs with Bot icon, bg-background or error styling
    this.lastAssistantMessage = this.messagesContainer.locator('div.bg-background, div.bg-destructive\\/10, div.border').filter({ has: page.locator('svg') }).last();
    // Retry button appears in error state - button with RefreshCw icon or "Retry" text
    this.retryButton = page.getByRole('button', { name: /retry/i });
    // Error messages appear in red/border-destructive styling
    this.errorMessage = page.locator('.bg-destructive\\/10, .bg-destructive\\/15, [role="alert"]');
    // Sources are in a details element with "Sources (N)" summary
    this.sourcesContainer = page.locator('details:has(summary:has-text("Sources"))');
    // Loading indicator - shows "Thinking..." text or spinner
    this.loadingIndicator = page.locator('text=Thinking').or(page.locator('.animate-spin')).or(page.locator('.loader'));
    // Suggested prompts are buttons in the empty state with text-left class
    this.suggestedPrompts = page.locator('button.text-left.text-sm.text-primary, .space-y-2 button.text-left');
    // Session history not currently in UI
    this.sessionHistory = page.locator('aside, [data-testid="session-history"]');
  }

  /**
   * Navigate to the chat page.
   */
  async navigate(): Promise<void> {
    await this.page.goto('/chat');
    // Wait for the chat interface to be visible
    await expect(this.messageInput).toBeVisible({ timeout: 10000 });
  }

  /**
   * Send a message in the chat.
   */
  async sendMessage(message: string): Promise<void> {
    await this.messageInput.fill(message);
    await this.sendButton.click();
  }

  /**
   * Send a message and wait for response.
   */
  async sendMessageAndWaitForResponse(message: string): Promise<void> {
    await this.sendMessage(message);
    await this.waitForResponse();
  }

  /**
   * Wait for the assistant response to appear.
   */
  async waitForResponse(): Promise<void> {
    // Wait for loading to start and then complete
    await expect(this.loadingIndicator.or(this.lastAssistantMessage)).toBeVisible({ timeout: 5000 });
    // Wait for the response to complete (loading indicator disappears or response appears)
    await expect(this.lastAssistantMessage).toBeVisible({ timeout: 30000 });
  }

  /**
   * Get the last assistant message text.
   */
  async getLastAssistantMessageText(): Promise<string> {
    await expect(this.lastAssistantMessage).toBeVisible({ timeout: 5000 });
    return (await this.lastAssistantMessage.textContent()) || '';
  }

  /**
   * Check if the last message contains expected text.
   */
  async lastMessageContains(text: string): Promise<boolean> {
    const messageText = await this.getLastAssistantMessageText();
    return messageText.toLowerCase().includes(text.toLowerCase());
  }

  /**
   * Wait for and click the retry button.
   */
  async retry(): Promise<void> {
    await expect(this.retryButton).toBeVisible({ timeout: 5000 });
    await this.retryButton.click();
  }

  /**
   * Check if error is displayed.
   */
  async hasError(): Promise<boolean> {
    return await this.errorMessage.isVisible();
  }

  /**
   * Get the error message text.
   */
  async getErrorMessage(): Promise<string> {
    return (await this.errorMessage.textContent()) || '';
  }

  /**
   * Check if sources are displayed.
   */
  async hasSources(): Promise<boolean> {
    return await this.sourcesContainer.isVisible();
  }

  /**
   * Get the number of displayed sources.
   */
  async getSourceCount(): Promise<number> {
    if (!await this.hasSources()) return 0;
    const sources = this.sourcesContainer.locator('[data-testid="source-item"], .source-item, li');
    return await sources.count();
  }

  /**
   * Click on a source to view property details.
   */
  async clickSource(index: number = 0): Promise<void> {
    const sources = this.sourcesContainer.locator('[data-testid="source-item"], .source-item, li');
    const source = sources.nth(index);
    if (await source.isVisible()) {
      await source.click();
    }
  }

  /**
   * Check if suggested prompts are displayed.
   */
  async hasSuggestedPrompts(): Promise<boolean> {
    const count = await this.suggestedPrompts.count();
    return count > 0;
  }

  /**
   * Click on a suggested prompt.
   */
  async clickSuggestedPrompt(index: number = 0): Promise<void> {
    // The suggested prompts ARE the buttons themselves
    const prompt = this.suggestedPrompts.nth(index);
    if (await prompt.isVisible()) {
      await prompt.click();
    }
  }

  /**
   * Get all user messages in the conversation.
   */
  async getUserMessages(): Promise<string[]> {
    const userMessages = this.messagesContainer.locator('[data-testid="user-message"], .user-message');
    const count = await userMessages.count();
    const messages: string[] = [];
    for (let i = 0; i < count; i++) {
      messages.push((await userMessages.nth(i).textContent()) || '');
    }
    return messages;
  }

  /**
   * Get all assistant messages in the conversation.
   */
  async getAssistantMessages(): Promise<string[]> {
    const assistantMessages = this.messagesContainer.locator('[data-testid="assistant-message"], .assistant-message');
    const count = await assistantMessages.count();
    const messages: string[] = [];
    for (let i = 0; i < count; i++) {
      messages.push((await assistantMessages.nth(i).textContent()) || '');
    }
    return messages;
  }

  /**
   * Clear the chat session (if button exists).
   */
  async clearSession(): Promise<void> {
    const clearButton = this.page.getByRole('button', { name: /clear|new chat|reset/i });
    if (await clearButton.isVisible()) {
      await clearButton.click();
    }
  }
}
