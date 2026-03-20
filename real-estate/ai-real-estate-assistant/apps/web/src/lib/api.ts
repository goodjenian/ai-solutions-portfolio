import {
  ChatRequest,
  ChatResponse,
  Collection,
  CollectionCreate,
  CollectionListResponse,
  CollectionUpdate,
  ExcelSheetsRequest,
  ExcelSheetsResponse,
  Favorite,
  FavoriteCheckResponse,
  FavoriteCreate,
  FavoriteListResponse,
  FavoriteUpdate,
  IngestRequest,
  IngestResponse,
  InvestmentAnalysisInput,
  InvestmentAnalysisResult,
  MarketIndicators,
  MarketTrends,
  ModelProviderCatalog,
  ModelPreferences,
  ModelRuntimeTestResponse,
  MortgageInput,
  MortgageResult,
  TCOInput,
  TCOResult,
  NeighborhoodQualityInput,
  NeighborhoodQualityResult,
  NotificationSettings,
  PortalFiltersRequest,
  PortalIngestResponse,
  PortalAdaptersResponse,
  PriceHistory,
  RagQaRequest,
  RagQaResponse,
  RagResetResponse,
  RagUploadResponse,
  SavedSearch,
  SavedSearchCreate,
  SavedSearchListResponse,
  SavedSearchUpdate,
  SearchRequest,
  SearchResponse,
  ExportFormat,
  ExportPropertiesRequest,
  PromptTemplateApplyResponse,
  PromptTemplateInfo,
  // Task #39: Advanced Investment Analytics
  AdvancedInvestmentInput,
  AdvancedInvestmentResult,
  PortfolioAnalysisInput,
  PortfolioAnalysisResult,
  // Task #42: Rent vs Buy Calculator
  RentVsBuyInput,
  RentVsBuyResult,
  // Task #52: Enhanced TCO Calculator
  TCOComparisonInput,
  TCOComparisonResult,
  TCOLocationDefaults,
  AvailableLocationsResponse,
  // Task #54: Listing Generation
  ListingGenerationRequest,
  ListingGenerationResult,
  // Task #51: Commute Time Analysis
  CommuteTimeRequest,
  CommuteTimeResponse,
  CommuteRankingRequest,
  CommuteRankingResponse,
  // Task #53: Market Anomaly Detection
  MarketAnomaly,
  AnomalyListResponse,
  AnomalyStatsResponse,
  AnomalyDismissRequest,
  AnomalyFilterParams,
  // Task #55: Lead Scoring System
  Lead,
  LeadWithScore,
  LeadScoreBreakdown,
  AgentAssignment,
  LeadListResponse,
  LeadDetailResponse,
  LeadFilters,
  LeadStatus,
  BulkAssignRequest,
  BulkStatusUpdateRequest,
  BulkOperationResponse,
  RecalculateScoresRequest,
  RecalculateScoresResponse,
  ScoringStatistics,
  // Task #56: Agent Performance Analytics
  Deal,
  DealCreate,
  DealStatus,
  DealListResponse,
  AgentMetrics,
  TeamComparison,
  PerformanceTrendsResponse,
  CoachingInsightsResponse,
  GoalProgressListResponse,
  TopPerformersResponse,
  AgentsNeedingSupportResponse,
  // Task #45: Agent/Broker Integration
  AgentProfile,
  AgentProfileCreate,
  AgentProfileUpdate,
  AgentProfileListResponse,
  AgentListing,
  AgentListingListResponse,
  AgentInquiry,
  AgentInquiryCreate,
  AgentInquiryUpdate,
  AgentInquiryListResponse,
  ViewingAppointment,
  ViewingAppointmentCreate,
  ViewingAppointmentUpdate,
  ViewingAppointmentListResponse,
  AgentFilters,
  // Task #43: Document Management
  Document,
  DocumentUploadResponse,
  DocumentListResponse,
  DocumentUpdateRequest,
  DocumentFilters,
  ExpiringDocumentsResponse,
  // Task #57: E-Signature Integration
  SignatureRequest,
  SignatureRequestCreate,
  SignatureRequestListResponse,
  SignatureRequestFilters,
  Signer,
  DocumentTemplate,
  DocumentTemplateCreate,
  DocumentTemplateUpdate,
  DocumentTemplateListResponse,
  SignedDocument,
} from './types';

function getApiUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL || '/api/v1';
}

function getUserEmail(): string | undefined {
  if (typeof window === 'undefined') return undefined;
  const email = window.localStorage.getItem('userEmail');
  return email && email.trim() ? email.trim() : undefined;
}

function buildAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};

  const userEmail = getUserEmail();
  if (userEmail) headers['X-User-Email'] = userEmail;

  return headers;
}

function buildHeaders(extra?: Record<string, string>): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  return { ...headers, ...buildAuthHeaders(), ...(extra || {}) };
}

function buildMultipartHeaders(extra?: Record<string, string>): Record<string, string> {
  return { ...buildAuthHeaders(), ...(extra || {}) };
}

/**
 * Error category for classification and handling.
 */
export type ApiErrorCategory =
  | 'network' // Connection failed, offline, DNS issues
  | 'timeout' // Request timed out
  | 'auth' // 401/403 authentication/authorization errors
  | 'validation' // 400/422 client-side validation errors
  | 'not_found' // 404 resource not found
  | 'rate_limit' // 429 too many requests
  | 'server' // 500+ server-side errors
  | 'unknown'; // Unclassified errors

/**
 * Custom error class for API errors that includes request_id for correlation
 * and error categorization for better handling strategies.
 *
 * @example
 * ```ts
 * try {
 *   await searchProperties({ query: "test" });
 * } catch (e) {
 *   if (e instanceof ApiError) {
 *     if (e.isRetryable) {
 *       // Implement retry logic
 *     }
 *     if (e.category === "auth") {
 *       // Redirect to login
 *     }
 *   }
 * }
 * ```
 */
export class ApiError extends Error {
  public readonly category: ApiErrorCategory;
  public readonly isRetryable: boolean;

  constructor(
    message: string,
    public readonly status: number,
    public readonly request_id?: string,
    category?: ApiErrorCategory
  ) {
    super(message);
    this.name = 'ApiError';

    // Determine category if not provided
    this.category = category ?? ApiError.categorizeStatus(status);

    // Determine if error is retryable
    this.isRetryable = ApiError.isRetryableCategory(this.category, status);
  }

  /**
   * Categorize error based on HTTP status code.
   */
  static categorizeStatus(status: number): ApiErrorCategory {
    if (status === 0) return 'network';
    if (status === 401 || status === 403) return 'auth';
    if (status === 404) return 'not_found';
    if (status === 408 || status === 504) return 'timeout';
    if (status === 429) return 'rate_limit';
    if (status === 400 || status === 422) return 'validation';
    if (status >= 500) return 'server';
    return 'unknown';
  }

  /**
   * Determine if an error category is generally retryable.
   * Network errors, timeouts, rate limits, and some server errors may be retried.
   */
  static isRetryableCategory(category: ApiErrorCategory, status: number): boolean {
    switch (category) {
      case 'network':
      case 'timeout':
      case 'rate_limit':
        return true;
      case 'server':
        // 503 Service Unavailable and 502 Bad Gateway are often transient
        return status === 502 || status === 503;
      default:
        return false;
    }
  }

  /**
   * Create a network error (for fetch failures, offline, etc.)
   */
  static networkError(originalError?: Error): ApiError {
    const message = originalError?.message || 'Network request failed. Check your connection.';
    const error = new ApiError(message, 0, undefined, 'network');
    if (originalError) {
      error.cause = originalError;
    }
    return error;
  }

  /**
   * Create a timeout error.
   */
  static timeoutError(request_id?: string): ApiError {
    return new ApiError('Request timed out. Please try again.', 408, request_id, 'timeout');
  }
}

/**
 * Safely perform a fetch request with network error handling.
 * Wraps fetch to convert network failures into ApiError.
 */
async function safeFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(input, init);
  } catch (error) {
    // Network errors (offline, DNS, CORS, etc.)
    throw ApiError.networkError(error instanceof Error ? error : undefined);
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text().catch(() => '');
    const headers = (response as unknown as { headers?: { get?: (name: string) => string | null } })
      .headers;
    const requestId =
      headers && typeof headers.get === 'function'
        ? headers.get('X-Request-ID') || undefined
        : undefined;
    let message = 'API request failed';
    if (errorText) {
      try {
        const parsed: unknown = JSON.parse(errorText);
        if (parsed && typeof parsed === 'object') {
          const detail = (parsed as { detail?: unknown }).detail;
          if (typeof detail === 'string' && detail.trim()) {
            message = detail.trim();
          } else if (detail !== undefined) {
            message = JSON.stringify(detail);
          } else {
            message = errorText;
          }
        } else {
          message = errorText;
        }
      } catch {
        message = errorText;
      }
    }
    throw new ApiError(message, response.status, requestId || undefined);
  }
  return response.json();
}

export async function getNotificationSettings(): Promise<NotificationSettings> {
  const response = await safeFetch(`${getApiUrl()}/settings/notifications`, {
    method: 'GET',
    headers: {
      ...buildHeaders(),
    },
  });
  return handleResponse<NotificationSettings>(response);
}

export async function updateNotificationSettings(
  settings: NotificationSettings
): Promise<NotificationSettings> {
  const response = await fetch(`${getApiUrl()}/settings/notifications`, {
    method: 'PUT',
    headers: {
      ...buildHeaders(),
    },
    body: JSON.stringify(settings),
  });
  return handleResponse<NotificationSettings>(response);
}

export async function getModelsCatalog(): Promise<ModelProviderCatalog[]> {
  const response = await fetch(`${getApiUrl()}/settings/models`, {
    method: 'GET',
    headers: {
      ...buildHeaders(),
    },
  });
  return handleResponse<ModelProviderCatalog[]>(response);
}

export async function testModelRuntime(provider: string): Promise<ModelRuntimeTestResponse> {
  const response = await fetch(
    `${getApiUrl()}/settings/test-runtime?provider=${encodeURIComponent(provider)}`,
    {
      method: 'GET',
      headers: {
        ...buildHeaders(),
      },
    }
  );
  return handleResponse<ModelRuntimeTestResponse>(response);
}

export async function getModelPreferences(): Promise<ModelPreferences> {
  const response = await fetch(`${getApiUrl()}/settings/model-preferences`, {
    method: 'GET',
    headers: {
      ...buildHeaders(),
    },
  });
  return handleResponse<ModelPreferences>(response);
}

export async function updateModelPreferences(
  payload: Partial<ModelPreferences>
): Promise<ModelPreferences> {
  const response = await fetch(`${getApiUrl()}/settings/model-preferences`, {
    method: 'PUT',
    headers: {
      ...buildHeaders(),
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<ModelPreferences>(response);
}

export async function calculateMortgage(input: MortgageInput): Promise<MortgageResult> {
  const response = await fetch(`${getApiUrl()}/tools/mortgage-calculator`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify(input),
  });
  return handleResponse<MortgageResult>(response);
}

export async function calculateTCO(input: TCOInput): Promise<TCOResult> {
  const response = await fetch(`${getApiUrl()}/tools/tco-calculator`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify(input),
  });
  return handleResponse<TCOResult>(response);
}

// Task #52: TCO Comparison API
export async function compareTCO(input: TCOComparisonInput): Promise<TCOComparisonResult> {
  const response = await fetch(`${getApiUrl()}/tools/tco-comparison`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify(input),
  });
  return handleResponse<TCOComparisonResult>(response);
}

// Task #52: Location Defaults API
export async function getTCOLocationDefaults(
  country: string,
  region?: string
): Promise<TCOLocationDefaults> {
  const params = new URLSearchParams({ country });
  if (region) {
    params.append('region', region);
  }
  const response = await fetch(`${getApiUrl()}/tools/tco-location-defaults?${params.toString()}`, {
    method: 'GET',
    headers: buildHeaders(),
  });
  return handleResponse<TCOLocationDefaults>(response);
}

export async function getTCOAvailableLocations(): Promise<AvailableLocationsResponse> {
  const response = await fetch(`${getApiUrl()}/tools/tco-available-locations`, {
    method: 'GET',
    headers: buildHeaders(),
  });
  return handleResponse<AvailableLocationsResponse>(response);
}

export async function calculateInvestment(
  input: InvestmentAnalysisInput
): Promise<InvestmentAnalysisResult> {
  const response = await fetch(`${getApiUrl()}/tools/investment-analysis`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify(input),
  });
  return handleResponse<InvestmentAnalysisResult>(response);
}

export async function neighborhoodQualityApi(
  input: NeighborhoodQualityInput
): Promise<NeighborhoodQualityResult> {
  const response = await fetch(`${getApiUrl()}/tools/neighborhood-quality`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify(input),
  });
  return handleResponse<NeighborhoodQualityResult>(response);
}

/**
 * Convenience function to get neighborhood badge data for a property.
 * Can be used directly on property cards with property data.
 *
 * @param property - Property object with id, latitude, longitude, city, neighborhood
 * @returns Neighborhood quality result for badge display
 */
export async function getNeighborhoodBadge(property: {
  id?: string;
  latitude?: number;
  longitude?: number;
  city?: string;
  neighborhood?: string;
}): Promise<NeighborhoodQualityResult> {
  return neighborhoodQualityApi({
    property_id: property.id || 'unknown',
    latitude: property.latitude,
    longitude: property.longitude,
    city: property.city,
    neighborhood: property.neighborhood,
  });
}

export async function comparePropertiesApi(propertyIds: string[]) {
  const response = await fetch(`${getApiUrl()}/tools/compare-properties`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify({ property_ids: propertyIds }),
  });
  return handleResponse<{
    properties: Array<{
      id?: string;
      price?: number;
      price_per_sqm?: number;
      city?: string;
      rooms?: number;
      bathrooms?: number;
      area_sqm?: number;
      year_built?: number;
      property_type?: string;
    }>;
    summary: { count: number; min_price?: number; max_price?: number; price_difference?: number };
  }>(response);
}

export async function priceAnalysisApi(query: string) {
  const response = await fetch(`${getApiUrl()}/tools/price-analysis`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify({ query }),
  });
  return handleResponse<{
    query: string;
    count: number;
    average_price?: number;
    median_price?: number;
    min_price?: number;
    max_price?: number;
    average_price_per_sqm?: number;
    median_price_per_sqm?: number;
    distribution_by_type: Record<string, number>;
  }>(response);
}

export async function locationAnalysisApi(propertyId: string) {
  const response = await fetch(`${getApiUrl()}/tools/location-analysis`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify({ property_id: propertyId }),
  });
  return handleResponse<{
    property_id: string;
    city?: string;
    neighborhood?: string;
    lat?: number;
    lon?: number;
  }>(response);
}

export async function valuationApi(propertyId: string) {
  const response = await fetch(`${getApiUrl()}/tools/valuation`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify({ property_id: propertyId }),
  });
  return handleResponse<{ property_id: string; estimated_value: number }>(response);
}

export async function legalCheckApi(text: string) {
  const response = await fetch(`${getApiUrl()}/tools/legal-check`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify({ text }),
  });
  return handleResponse<{ risks: Array<Record<string, unknown>>; score: number }>(response);
}

export async function enrichAddressApi(address: string) {
  const response = await fetch(`${getApiUrl()}/tools/enrich-address`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify({ address }),
  });
  return handleResponse<{ address: string; data: Record<string, unknown> }>(response);
}

export async function listPromptTemplates(): Promise<PromptTemplateInfo[]> {
  const response = await fetch(`${getApiUrl()}/prompt-templates`, {
    method: 'GET',
    headers: buildHeaders(),
  });
  return handleResponse<PromptTemplateInfo[]>(response);
}

export async function applyPromptTemplate(
  templateId: string,
  variables: Record<string, unknown>
): Promise<PromptTemplateApplyResponse> {
  const response = await fetch(`${getApiUrl()}/prompt-templates/apply`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify({ template_id: templateId, variables }),
  });
  return handleResponse<PromptTemplateApplyResponse>(response);
}

export async function uploadRagDocuments(files: File[]): Promise<RagUploadResponse> {
  const formData = new FormData();
  for (const file of files) {
    formData.append('files', file, file.name);
  }

  const response = await fetch(`${getApiUrl()}/rag/upload`, {
    method: 'POST',
    headers: buildMultipartHeaders(),
    body: formData,
  });
  return handleResponse<RagUploadResponse>(response);
}

export async function resetRagKnowledge(): Promise<RagResetResponse> {
  const response = await fetch(`${getApiUrl()}/rag/reset`, {
    method: 'POST',
    headers: buildHeaders(),
  });
  return handleResponse<RagResetResponse>(response);
}

export async function ragQa(request: RagQaRequest): Promise<RagQaResponse> {
  const response = await fetch(`${getApiUrl()}/rag/qa`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify(request),
  });
  return handleResponse<RagQaResponse>(response);
}

export async function crmSyncContactApi(name: string, phone?: string, email?: string) {
  const response = await fetch(`${getApiUrl()}/tools/crm-sync-contact`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify({ name, phone, email }),
  });
  return handleResponse<{ id: string }>(response);
}

export async function searchProperties(request: SearchRequest): Promise<SearchResponse> {
  const response = await safeFetch(`${getApiUrl()}/search`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify(request),
  });
  return handleResponse<SearchResponse>(response);
}

export async function chatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await safeFetch(`${getApiUrl()}/chat`, {
    method: 'POST',
    headers: {
      ...buildHeaders(),
    },
    body: JSON.stringify(request),
  });
  return handleResponse<ChatResponse>(response);
}

export async function streamChatMessage(
  request: ChatRequest,
  onChunk: (chunk: string) => void,
  onStart?: (meta: { requestId?: string }) => void,
  onMeta?: (meta: {
    sources?: ChatResponse['sources'];
    sourcesTruncated?: boolean;
    sessionId?: string;
    intermediateSteps?: ChatResponse['intermediate_steps'];
  }) => void
): Promise<void> {
  const response = await safeFetch(`${getApiUrl()}/chat`, {
    method: 'POST',
    headers: {
      ...buildHeaders(),
    },
    body: JSON.stringify({ ...request, stream: true }),
  });

  if (!response.ok || !response.body) {
    const errorText = await response.text().catch(() => '');
    const headers = (response as unknown as { headers?: { get?: (name: string) => string | null } })
      .headers;
    const requestId =
      headers && typeof headers.get === 'function'
        ? headers.get('X-Request-ID') || undefined
        : undefined;
    const message = errorText || 'Failed to start stream';
    throw new ApiError(message, response.status, requestId || undefined);
  }

  const requestId = response.headers.get('X-Request-ID') || undefined;
  if (onStart) {
    onStart({ requestId });
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value);
    while (true) {
      const boundaryIndex = buffer.indexOf('\n\n');
      if (boundaryIndex === -1) break;
      const rawEvent = buffer.slice(0, boundaryIndex);
      buffer = buffer.slice(boundaryIndex + 2);

      let eventName = 'message';
      const dataLines: string[] = [];
      for (const rawLine of rawEvent.split('\n')) {
        const line = rawLine.trimEnd();
        if (!line) continue;
        if (line.startsWith('event:')) {
          eventName = line.slice(6).trim() || 'message';
          continue;
        }
        if (line.startsWith('data:')) {
          dataLines.push(line.slice(5).trimStart());
        }
      }

      const data = dataLines.join('\n');
      if (!data) continue;
      if (data === '[DONE]') return;

      let parsed: unknown = undefined;
      try {
        parsed = JSON.parse(data);
      } catch {
        parsed = undefined;
      }

      if (parsed && typeof parsed === 'object') {
        const maybeError = (parsed as { error?: unknown }).error;
        if (typeof maybeError === 'string' && maybeError.trim()) {
          throw new Error(maybeError);
        }

        if (eventName === 'meta') {
          if (onMeta) {
            const sources = (parsed as { sources?: unknown }).sources;
            const sourcesTruncated = (parsed as { sources_truncated?: unknown }).sources_truncated;
            const sessionId = (parsed as { session_id?: unknown }).session_id;
            const intermediateSteps = (parsed as { intermediate_steps?: unknown })
              .intermediate_steps;
            onMeta({
              sources: Array.isArray(sources) ? (sources as ChatResponse['sources']) : undefined,
              sourcesTruncated:
                typeof sourcesTruncated === 'boolean' ? sourcesTruncated : undefined,
              sessionId: typeof sessionId === 'string' && sessionId.trim() ? sessionId : undefined,
              intermediateSteps: Array.isArray(intermediateSteps)
                ? (intermediateSteps as ChatResponse['intermediate_steps'])
                : undefined,
            });
          }
          continue;
        }

        const content = (parsed as { content?: unknown }).content;
        if (typeof content === 'string') {
          onChunk(content);
          continue;
        }
      }

      onChunk(data);
    }
  }
}

async function exportProperties(
  request: ExportPropertiesRequest
): Promise<{ filename: string; blob: Blob }> {
  const response = await fetch(`${getApiUrl()}/export/properties`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const errorText = await response.text().catch(() => '');
    const requestId = response.headers.get('X-Request-ID') || undefined;
    const errorMsg = errorText || 'Export request failed';
    throw new ApiError(errorMsg, response.status, requestId || undefined);
  }
  const cd = response.headers.get('Content-Disposition') || '';
  let filename = `properties.${request.format}`;
  const match = cd.match(/filename="([^"]+)"/i);
  if (match && match[1]) {
    filename = match[1];
  }
  const blob = await response.blob();
  return { filename, blob };
}

export async function exportPropertiesBySearch(
  search: SearchRequest,
  format: ExportFormat,
  options?: Pick<
    ExportPropertiesRequest,
    'columns' | 'include_header' | 'csv_delimiter' | 'csv_decimal'
  >
): Promise<{ filename: string; blob: Blob }> {
  return exportProperties({ format, search, ...(options || {}) });
}

export async function exportPropertiesByIds(
  propertyIds: string[],
  format: ExportFormat,
  options?: Pick<
    ExportPropertiesRequest,
    'columns' | 'include_header' | 'csv_delimiter' | 'csv_decimal'
  >
): Promise<{ filename: string; blob: Blob }> {
  return exportProperties({ format, property_ids: propertyIds, ...(options || {}) });
}

// Admin API functions for data ingestion
export async function ingestData(request: IngestRequest): Promise<IngestResponse> {
  const response = await fetch(`${getApiUrl()}/admin/ingest`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify(request),
  });
  return handleResponse<IngestResponse>(response);
}

export async function getExcelSheets(request: ExcelSheetsRequest): Promise<ExcelSheetsResponse> {
  const response = await fetch(`${getApiUrl()}/admin/excel/sheets`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify(request),
  });
  return handleResponse<ExcelSheetsResponse>(response);
}

// File upload API functions for Task #48
export async function ingestFileUpload(
  file: File,
  options?: {
    sheet_name?: string;
    header_row?: number;
    source_name?: string;
  }
): Promise<IngestResponse> {
  const formData = new FormData();
  formData.append('file', file, file.name);
  if (options?.sheet_name) formData.append('sheet_name', options.sheet_name);
  formData.append('header_row', String(options?.header_row ?? 0));
  if (options?.source_name) formData.append('source_name', options.source_name);

  const response = await fetch(`${getApiUrl()}/admin/ingest/upload`, {
    method: 'POST',
    headers: buildMultipartHeaders(),
    body: formData,
  });
  return handleResponse<IngestResponse>(response);
}

export async function getExcelSheetsUpload(file: File): Promise<ExcelSheetsResponse> {
  const formData = new FormData();
  formData.append('file', file, file.name);

  const response = await fetch(`${getApiUrl()}/admin/excel/sheets/upload`, {
    method: 'POST',
    headers: buildMultipartHeaders(),
    body: formData,
  });
  return handleResponse<ExcelSheetsResponse>(response);
}

// Portal/API Integration functions for TASK-006
export async function listPortals(): Promise<PortalAdaptersResponse> {
  const response = await fetch(`${getApiUrl()}/admin/portals`, {
    method: 'GET',
    headers: buildHeaders(),
  });
  return handleResponse<PortalAdaptersResponse>(response);
}

export async function fetchFromPortal(
  request: PortalFiltersRequest
): Promise<PortalIngestResponse> {
  const response = await fetch(`${getApiUrl()}/admin/portals/fetch`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify(request),
  });
  return handleResponse<PortalIngestResponse>(response);
}

// Saved Searches API functions for Task #36
export async function getSavedSearches(
  includeInactive: boolean = false
): Promise<SavedSearchListResponse> {
  const url = `${getApiUrl()}/saved-searches?include_inactive=${includeInactive}`;
  const response = await safeFetch(url, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<SavedSearchListResponse>(response);
}

export async function createSavedSearch(data: SavedSearchCreate): Promise<SavedSearch> {
  const response = await safeFetch(`${getApiUrl()}/saved-searches`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(data),
  });
  return handleResponse<SavedSearch>(response);
}

export async function getSavedSearch(id: string): Promise<SavedSearch> {
  const response = await safeFetch(`${getApiUrl()}/saved-searches/${id}`, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<SavedSearch>(response);
}

export async function updateSavedSearch(id: string, data: SavedSearchUpdate): Promise<SavedSearch> {
  const response = await safeFetch(`${getApiUrl()}/saved-searches/${id}`, {
    method: 'PATCH',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(data),
  });
  return handleResponse<SavedSearch>(response);
}

export async function deleteSavedSearch(id: string): Promise<void> {
  const response = await safeFetch(`${getApiUrl()}/saved-searches/${id}`, {
    method: 'DELETE',
    headers: buildHeaders(),
    credentials: 'include',
  });
  if (!response.ok) {
    const errorText = await response.text().catch(() => '');
    const requestId = response.headers.get('X-Request-ID') || undefined;
    throw new ApiError(
      errorText || 'Failed to delete saved search',
      response.status,
      requestId || undefined
    );
  }
}

export async function toggleSavedSearchAlert(id: string, enabled: boolean): Promise<SavedSearch> {
  const response = await safeFetch(
    `${getApiUrl()}/saved-searches/${id}/toggle-alert?enabled=${enabled}`,
    {
      method: 'POST',
      headers: buildHeaders(),
      credentials: 'include',
    }
  );
  return handleResponse<SavedSearch>(response);
}

export async function markSavedSearchUsed(id: string): Promise<SavedSearch> {
  const response = await safeFetch(`${getApiUrl()}/saved-searches/${id}/use`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<SavedSearch>(response);
}

// Favorites API functions for Task #37
export async function getFavorites(
  collectionId?: string,
  limit: number = 50,
  offset: number = 0
): Promise<FavoriteListResponse> {
  const params = new URLSearchParams();
  if (collectionId) params.append('collection_id', collectionId);
  params.append('limit', String(limit));
  params.append('offset', String(offset));

  const response = await safeFetch(`${getApiUrl()}/favorites?${params}`, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<FavoriteListResponse>(response);
}

export async function addFavorite(data: FavoriteCreate): Promise<Favorite> {
  const response = await safeFetch(`${getApiUrl()}/favorites`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(data),
  });
  return handleResponse<Favorite>(response);
}

export async function removeFavorite(favoriteId: string): Promise<void> {
  const response = await safeFetch(`${getApiUrl()}/favorites/${favoriteId}`, {
    method: 'DELETE',
    headers: buildHeaders(),
    credentials: 'include',
  });
  if (!response.ok) {
    const errorText = await response.text().catch(() => '');
    throw new ApiError(errorText || 'Failed to remove favorite', response.status);
  }
}

export async function removeFavoriteByProperty(propertyId: string): Promise<void> {
  const response = await safeFetch(`${getApiUrl()}/favorites/by-property/${propertyId}`, {
    method: 'DELETE',
    headers: buildHeaders(),
    credentials: 'include',
  });
  if (!response.ok) {
    const errorText = await response.text().catch(() => '');
    throw new ApiError(errorText || 'Failed to remove favorite', response.status);
  }
}

export async function checkFavorite(propertyId: string): Promise<FavoriteCheckResponse> {
  const response = await safeFetch(`${getApiUrl()}/favorites/check/${propertyId}`, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<FavoriteCheckResponse>(response);
}

export async function getFavoriteIds(): Promise<string[]> {
  const response = await safeFetch(`${getApiUrl()}/favorites/ids`, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<string[]>(response);
}

export async function updateFavorite(favoriteId: string, data: FavoriteUpdate): Promise<Favorite> {
  const response = await safeFetch(`${getApiUrl()}/favorites/${favoriteId}`, {
    method: 'PATCH',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(data),
  });
  return handleResponse<Favorite>(response);
}

export async function moveFavoriteToCollection(
  favoriteId: string,
  collectionId: string
): Promise<Favorite> {
  const response = await safeFetch(`${getApiUrl()}/favorites/${favoriteId}/move/${collectionId}`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<Favorite>(response);
}

// Collections API functions for Task #37
export async function getCollections(): Promise<CollectionListResponse> {
  const response = await safeFetch(`${getApiUrl()}/collections`, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<CollectionListResponse>(response);
}

export async function createCollection(data: CollectionCreate): Promise<Collection> {
  const response = await safeFetch(`${getApiUrl()}/collections`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(data),
  });
  return handleResponse<Collection>(response);
}

export async function getDefaultCollection(): Promise<Collection> {
  const response = await safeFetch(`${getApiUrl()}/collections/default`, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<Collection>(response);
}

export async function getCollection(id: string): Promise<Collection> {
  const response = await safeFetch(`${getApiUrl()}/collections/${id}`, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<Collection>(response);
}

export async function updateCollection(id: string, data: CollectionUpdate): Promise<Collection> {
  const response = await safeFetch(`${getApiUrl()}/collections/${id}`, {
    method: 'PUT',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(data),
  });
  return handleResponse<Collection>(response);
}

export async function deleteCollection(id: string): Promise<void> {
  const response = await safeFetch(`${getApiUrl()}/collections/${id}`, {
    method: 'DELETE',
    headers: buildHeaders(),
    credentials: 'include',
  });
  if (!response.ok) {
    const errorText = await response.text().catch(() => '');
    throw new ApiError(errorText || 'Failed to delete collection', response.status);
  }
}

// Market API functions for Task #38: Price History & Trends
export async function getPriceHistory(
  propertyId: string,
  limit: number = 100
): Promise<PriceHistory> {
  const response = await safeFetch(
    `${getApiUrl()}/market/price-history/${encodeURIComponent(propertyId)}?limit=${limit}`,
    {
      method: 'GET',
      headers: buildHeaders(),
      credentials: 'include',
    }
  );
  return handleResponse<PriceHistory>(response);
}

export async function getMarketTrends(params: {
  city?: string;
  district?: string;
  interval?: 'month' | 'quarter' | 'year';
  months_back?: number;
}): Promise<MarketTrends> {
  const searchParams = new URLSearchParams();
  if (params.city) searchParams.append('city', params.city);
  if (params.district) searchParams.append('district', params.district);
  if (params.interval) searchParams.append('interval', params.interval);
  if (params.months_back) searchParams.append('months_back', String(params.months_back));

  const queryString = searchParams.toString();
  const url = queryString
    ? `${getApiUrl()}/market/trends?${queryString}`
    : `${getApiUrl()}/market/trends`;

  const response = await safeFetch(url, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<MarketTrends>(response);
}

export async function getMarketIndicators(city?: string): Promise<MarketIndicators> {
  const url = city
    ? `${getApiUrl()}/market/indicators?city=${encodeURIComponent(city)}`
    : `${getApiUrl()}/market/indicators`;

  const response = await safeFetch(url, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<MarketIndicators>(response);
}

// ============================================================================
// Task #39: Advanced Investment Analytics
// ============================================================================

/**
 * Calculate advanced investment analysis with multi-year projections,
 * tax implications, appreciation scenarios, and risk assessment.
 */
export async function calculateAdvancedInvestment(
  input: AdvancedInvestmentInput
): Promise<AdvancedInvestmentResult> {
  const response = await safeFetch(`${getApiUrl()}/tools/advanced-investment-analysis`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(input),
  });
  return handleResponse<AdvancedInvestmentResult>(response);
}

/**
 * Analyze a portfolio of investment properties including aggregate metrics,
 * diversification scores, and risk assessment.
 */
export async function analyzePortfolio(
  input: PortfolioAnalysisInput
): Promise<PortfolioAnalysisResult> {
  const response = await safeFetch(`${getApiUrl()}/tools/portfolio-analysis`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(input),
  });
  return handleResponse<PortfolioAnalysisResult>(response);
}

/**
 * Task #42: Calculate rent vs buy comparison.
 * Compares the financial implications of renting vs buying a property over time,
 * including break-even analysis, opportunity costs, and tax benefits.
 */
export async function calculateRentVsBuy(input: RentVsBuyInput): Promise<RentVsBuyResult> {
  const response = await safeFetch(`${getApiUrl()}/tools/rent-vs-buy`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(input),
  });
  return handleResponse<RentVsBuyResult>(response);
}

// ============================================================================
// Task #54: Listing Generation
// ============================================================================

/**
 * Generate AI-powered listing content for a property.
 *
 * Generates:
 * - Property description with customizable tone and language
 * - Multiple headline variants for different platforms
 * - Platform-specific social media content
 *
 * All generated content respects platform character limits.
 */
export async function generateListing(
  input: ListingGenerationRequest
): Promise<ListingGenerationResult> {
  const response = await safeFetch(`${getApiUrl()}/tools/generate-listing`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(input),
  });
  return handleResponse<ListingGenerationResult>(response);
}

// Task #51: Commute Time Analysis

/**
 * Calculate commute time from a single property to a destination.
 * Uses Google Routes API for accurate routing with real-time traffic.
 */
export async function calculateCommuteTime(
  input: CommuteTimeRequest
): Promise<CommuteTimeResponse> {
  const response = await safeFetch(`${getApiUrl()}/tools/commute-time`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(input),
  });
  return handleResponse<CommuteTimeResponse>(response);
}

/**
 * Rank multiple properties by commute time to a destination.
 * Returns properties sorted by commute duration (fastest first).
 */
export async function rankPropertiesByCommute(
  input: CommuteRankingRequest
): Promise<CommuteRankingResponse> {
  const response = await safeFetch(`${getApiUrl()}/tools/commute-ranking`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(input),
  });
  return handleResponse<CommuteRankingResponse>(response);
}

// ============================================================================
// Task #53: Market Anomaly Detection
// ============================================================================

/**
 * Get list of detected market anomalies with optional filters.
 *
 * Supports filtering by:
 * - severity: low, medium, high, critical
 * - anomaly_type: price_spike, price_drop, volume_spike, volume_drop, unusual_pattern
 * - scope_type: property, city, district, market, region
 * - scope_id: specific property/city/district ID
 */
export async function getAnomalies(params?: AnomalyFilterParams): Promise<AnomalyListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.append('limit', String(params.limit));
  if (params?.offset) searchParams.append('offset', String(params.offset));
  if (params?.severity) searchParams.append('severity', params.severity);
  if (params?.anomaly_type) searchParams.append('anomaly_type', params.anomaly_type);
  if (params?.scope_type) searchParams.append('scope_type', params.scope_type);
  if (params?.scope_id) searchParams.append('scope_id', params.scope_id);

  const queryString = searchParams.toString();
  const url = queryString ? `${getApiUrl()}/anomalies?${queryString}` : `${getApiUrl()}/anomalies`;

  const response = await safeFetch(url, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<AnomalyListResponse>(response);
}

/**
 * Get a single anomaly by ID with full details.
 */
export async function getAnomaly(id: string): Promise<MarketAnomaly> {
  const response = await safeFetch(`${getApiUrl()}/anomalies/${encodeURIComponent(id)}`, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<MarketAnomaly>(response);
}

/**
 * Dismiss an anomaly (mark as reviewed/acknowledged).
 *
 * Once dismissed, the anomaly won't trigger future alerts.
 */
export async function dismissAnomaly(
  id: string,
  request?: AnomalyDismissRequest
): Promise<MarketAnomaly> {
  const response = await safeFetch(`${getApiUrl()}/anomalies/${encodeURIComponent(id)}/dismiss`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(request || {}),
  });
  return handleResponse<MarketAnomaly>(response);
}

/**
 * Get anomaly statistics summary.
 *
 * Returns:
 * - Total anomalies
 * - Count by severity
 * - Count by type
 * - Undismissed count
 */
export async function getAnomalyStats(): Promise<AnomalyStatsResponse> {
  const response = await safeFetch(`${getApiUrl()}/anomalies/stats`, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<AnomalyStatsResponse>(response);
}

/**
 * Subscribe to real-time anomaly notifications via Server-Sent Events.
 *
 * Returns an EventSource that emits anomaly events as they're detected.
 *
 * @example
 * ```ts
 * const eventSource = subscribeToAnomalies();
 * eventSource.onmessage = (event) => {
 *   const anomaly = JSON.parse(event.data);
 *   console.log('New anomaly:', anomaly);
 * };
 *
 * // Don't forget to close when done
 * eventSource.close();
 * ```
 */
export function subscribeToAnomalies(): EventSource {
  const url = `${getApiUrl()}/anomalies/stream`;
  return new EventSource(url);
}

// ============================================
// Lead Scoring API (Task #55)
// ============================================

/**
 * Get list of leads with optional filters.
 *
 * Agents see only their assigned leads. Admins see all leads.
 */
export async function getLeads(
  params?: LeadFilters & { page?: number; page_size?: number }
): Promise<LeadListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.append('page', String(params.page));
  if (params?.page_size) searchParams.append('page_size', String(params.page_size));
  if (params?.status) searchParams.append('status', params.status);
  if (params?.score_min !== undefined) searchParams.append('score_min', String(params.score_min));
  if (params?.score_max !== undefined) searchParams.append('score_max', String(params.score_max));
  if (params?.source) searchParams.append('source', params.source);
  if (params?.has_email !== undefined) searchParams.append('has_email', String(params.has_email));
  if (params?.agent_id) searchParams.append('agent_id', params.agent_id);
  if (params?.sort_by) searchParams.append('sort_by', params.sort_by);
  if (params?.sort_order) searchParams.append('sort_order', params.sort_order);

  const queryString = searchParams.toString();
  const url = queryString ? `${getApiUrl()}/leads?${queryString}` : `${getApiUrl()}/leads`;

  const response = await safeFetch(url, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<LeadListResponse>(response);
}

/**
 * Get high-value leads (score >= threshold, default 70).
 */
export async function getHighValueLeads(threshold = 70, limit = 50): Promise<LeadWithScore[]> {
  const searchParams = new URLSearchParams();
  searchParams.append('threshold', String(threshold));
  searchParams.append('limit', String(limit));

  const response = await safeFetch(`${getApiUrl()}/leads/high-value?${searchParams}`, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<LeadWithScore[]>(response);
}

/**
 * Get detailed lead information including interactions and score history.
 */
export async function getLead(leadId: string): Promise<LeadDetailResponse> {
  const response = await safeFetch(`${getApiUrl()}/leads/${encodeURIComponent(leadId)}`, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<LeadDetailResponse>(response);
}

/**
 * Get lead score breakdown with factors and recommendations.
 */
export async function getLeadScoreBreakdown(leadId: string): Promise<LeadScoreBreakdown> {
  const response = await safeFetch(`${getApiUrl()}/leads/${encodeURIComponent(leadId)}/score`, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<LeadScoreBreakdown>(response);
}

/**
 * Update lead information.
 */
export async function updateLead(leadId: string, data: Partial<Lead>): Promise<Lead> {
  const response = await safeFetch(`${getApiUrl()}/leads/${encodeURIComponent(leadId)}`, {
    method: 'PATCH',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(data),
  });
  return handleResponse<Lead>(response);
}

/**
 * Update lead status.
 */
export async function updateLeadStatus(
  leadId: string,
  status: LeadStatus,
  notes?: string
): Promise<Lead> {
  const searchParams = new URLSearchParams();
  searchParams.append('status', status);
  if (notes) searchParams.append('notes', notes);

  const response = await safeFetch(
    `${getApiUrl()}/leads/${encodeURIComponent(leadId)}/status?${searchParams}`,
    {
      method: 'PATCH',
      headers: buildHeaders(),
      credentials: 'include',
    }
  );
  return handleResponse<Lead>(response);
}

/**
 * Assign an agent to a lead.
 */
export async function assignAgentToLead(
  leadId: string,
  agentId: string,
  options?: { notes?: string; is_primary?: boolean }
): Promise<AgentAssignment> {
  const response = await safeFetch(`${getApiUrl()}/leads/${encodeURIComponent(leadId)}/assign`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify({
      agent_id: agentId,
      notes: options?.notes,
      is_primary: options?.is_primary ?? true,
    }),
  });
  return handleResponse<AgentAssignment>(response);
}

/**
 * Bulk assign leads to an agent (admin only).
 */
export async function bulkAssignLeads(request: BulkAssignRequest): Promise<BulkOperationResponse> {
  const response = await safeFetch(`${getApiUrl()}/leads/bulk/assign`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(request),
  });
  return handleResponse<BulkOperationResponse>(response);
}

/**
 * Bulk update lead status (admin only).
 */
export async function bulkUpdateLeadStatus(
  request: BulkStatusUpdateRequest
): Promise<BulkOperationResponse> {
  const response = await safeFetch(`${getApiUrl()}/leads/bulk/status`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(request),
  });
  return handleResponse<BulkOperationResponse>(response);
}

/**
 * Recalculate lead scores (admin only).
 */
export async function recalculateScores(
  request?: RecalculateScoresRequest
): Promise<RecalculateScoresResponse> {
  const response = await safeFetch(`${getApiUrl()}/leads/scores/recalculate`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(request || {}),
  });
  return handleResponse<RecalculateScoresResponse>(response);
}

/**
 * Get scoring statistics (admin only).
 */
export async function getScoringStatistics(): Promise<ScoringStatistics> {
  const response = await safeFetch(`${getApiUrl()}/leads/scores/statistics`, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<ScoringStatistics>(response);
}

/**
 * Export leads to CSV (admin only).
 */
export async function exportLeads(params?: {
  status?: LeadStatus;
  score_min?: number;
}): Promise<Blob> {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.append('status', params.status);
  if (params?.score_min !== undefined) searchParams.append('score_min', String(params.score_min));

  const queryString = searchParams.toString();
  const url = queryString
    ? `${getApiUrl()}/leads/export?${queryString}`
    : `${getApiUrl()}/leads/export`;

  const response = await safeFetch(url, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Export failed' }));
    throw new ApiError(error.detail || 'Export failed', response.status);
  }

  return response.blob();
}

/**
 * Delete a lead (GDPR right to be forgotten, admin only).
 */
export async function deleteLead(leadId: string): Promise<{ message: string }> {
  const response = await safeFetch(`${getApiUrl()}/leads/${encodeURIComponent(leadId)}`, {
    method: 'DELETE',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<{ message: string }>(response);
}

// =============================================================================
// Agent Performance Analytics API (Task #56)
// =============================================================================

/**
 * Get current agent's performance metrics.
 */
export async function getAgentMetrics(params?: {
  period_start?: string;
  period_end?: string;
}): Promise<AgentMetrics> {
  const searchParams = new URLSearchParams();
  if (params?.period_start) searchParams.append('period_start', params.period_start);
  if (params?.period_end) searchParams.append('period_end', params.period_end);

  const queryString = searchParams.toString();
  const url = queryString
    ? `${getApiUrl()}/agent-analytics/me?${queryString}`
    : `${getApiUrl()}/agent-analytics/me`;

  const response = await safeFetch(url, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<AgentMetrics>(response);
}

/**
 * Get team comparison for current agent.
 */
export async function getTeamComparison(params?: {
  period_start?: string;
  period_end?: string;
}): Promise<TeamComparison> {
  const searchParams = new URLSearchParams();
  if (params?.period_start) searchParams.append('period_start', params.period_start);
  if (params?.period_end) searchParams.append('period_end', params.period_end);

  const queryString = searchParams.toString();
  const url = queryString
    ? `${getApiUrl()}/agent-analytics/me/comparison?${queryString}`
    : `${getApiUrl()}/agent-analytics/me/comparison`;

  const response = await safeFetch(url, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<TeamComparison>(response);
}

/**
 * Get performance trends over time.
 */
export async function getPerformanceTrends(params?: {
  interval?: 'day' | 'week' | 'month' | 'quarter';
  periods?: number;
}): Promise<PerformanceTrendsResponse> {
  const searchParams = new URLSearchParams();
  if (params?.interval) searchParams.append('interval', params.interval);
  if (params?.periods) searchParams.append('periods', String(params.periods));

  const response = await safeFetch(
    `${getApiUrl()}/agent-analytics/me/trends?${searchParams.toString()}`,
    {
      method: 'GET',
      headers: buildHeaders(),
      credentials: 'include',
    }
  );
  return handleResponse<PerformanceTrendsResponse>(response);
}

/**
 * Get coaching insights for current agent.
 */
export async function getCoachingInsights(): Promise<CoachingInsightsResponse> {
  const response = await safeFetch(`${getApiUrl()}/agent-analytics/me/insights`, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<CoachingInsightsResponse>(response);
}

/**
 * Get goal progress for current agent.
 */
export async function getGoalProgress(): Promise<GoalProgressListResponse> {
  const response = await safeFetch(`${getApiUrl()}/agent-analytics/me/goals`, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<GoalProgressListResponse>(response);
}

/**
 * Get top performers (admin only).
 */
export async function getTopPerformers(params?: {
  metric?: 'deals' | 'revenue' | 'conversion';
  limit?: number;
  period_days?: number;
}): Promise<TopPerformersResponse> {
  const searchParams = new URLSearchParams();
  if (params?.metric) searchParams.append('metric', params.metric);
  if (params?.limit) searchParams.append('limit', String(params.limit));
  if (params?.period_days) searchParams.append('period_days', String(params.period_days));

  const response = await safeFetch(
    `${getApiUrl()}/agent-analytics/top-performers?${searchParams.toString()}`,
    {
      method: 'GET',
      headers: buildHeaders(),
      credentials: 'include',
    }
  );
  return handleResponse<TopPerformersResponse>(response);
}

/**
 * Get agents needing support (admin only).
 */
export async function getAgentsNeedingSupport(params?: {
  threshold_days?: number;
}): Promise<AgentsNeedingSupportResponse> {
  const searchParams = new URLSearchParams();
  if (params?.threshold_days) searchParams.append('threshold_days', String(params.threshold_days));

  const response = await safeFetch(
    `${getApiUrl()}/agent-analytics/needs-support?${searchParams.toString()}`,
    {
      method: 'GET',
      headers: buildHeaders(),
      credentials: 'include',
    }
  );
  return handleResponse<AgentsNeedingSupportResponse>(response);
}

/**
 * Create a new deal.
 */
export async function createDeal(dealData: DealCreate): Promise<Deal> {
  const response = await safeFetch(`${getApiUrl()}/agent-analytics/deals`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(dealData),
  });
  return handleResponse<Deal>(response);
}

/**
 * Get deals for current agent.
 */
export async function getMyDeals(params?: {
  status?: DealStatus;
  page?: number;
  page_size?: number;
}): Promise<DealListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.append('status', params.status);
  if (params?.page) searchParams.append('page', String(params.page));
  if (params?.page_size) searchParams.append('page_size', String(params.page_size));

  const response = await safeFetch(
    `${getApiUrl()}/agent-analytics/deals?${searchParams.toString()}`,
    {
      method: 'GET',
      headers: buildHeaders(),
      credentials: 'include',
    }
  );
  return handleResponse<DealListResponse>(response);
}

/**
 * Get a specific deal by ID.
 */
export async function getDeal(dealId: string): Promise<Deal> {
  const response = await safeFetch(
    `${getApiUrl()}/agent-analytics/deals/${encodeURIComponent(dealId)}`,
    {
      method: 'GET',
      headers: buildHeaders(),
      credentials: 'include',
    }
  );
  return handleResponse<Deal>(response);
}

/**
 * Update a deal.
 */
export async function updateDeal(
  dealId: string,
  data: Partial<{
    status: DealStatus;
    deal_value: number;
    notes: string;
  }>
): Promise<Deal> {
  const response = await safeFetch(
    `${getApiUrl()}/agent-analytics/deals/${encodeURIComponent(dealId)}`,
    {
      method: 'PATCH',
      headers: buildHeaders(),
      credentials: 'include',
      body: JSON.stringify(data),
    }
  );
  return handleResponse<Deal>(response);
}

// =============================================================================
// Agent/Broker API (Task #45)
// =============================================================================

/**
 * Get list of agents with optional filters (public endpoint).
 */
export async function getAgents(
  params?: AgentFilters & { page?: number; page_size?: number }
): Promise<AgentProfileListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.append('page', String(params.page));
  if (params?.page_size) searchParams.append('page_size', String(params.page_size));
  if (params?.city) searchParams.append('city', params.city);
  if (params?.specialty) searchParams.append('specialty', params.specialty);
  if (params?.min_rating !== undefined) {
    searchParams.append('min_rating', String(params.min_rating));
  }
  if (params?.agency_id) searchParams.append('agency_id', params.agency_id);
  if (params?.sort_by) searchParams.append('sort_by', params.sort_by);
  if (params?.is_verified !== undefined) {
    searchParams.append('is_verified', String(params.is_verified));
  }
  if (params?.is_active !== undefined) {
    searchParams.append('is_active', String(params.is_active));
  }

  const queryString = searchParams.toString();
  const url = queryString ? `${getApiUrl()}/agents?${queryString}` : `${getApiUrl()}/agents`;

  const response = await safeFetch(url, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<AgentProfileListResponse>(response);
}

/**
 * Get a specific agent by ID (public endpoint).
 */
export async function getAgent(agentId: string): Promise<AgentProfile> {
  const response = await safeFetch(`${getApiUrl()}/agents/${encodeURIComponent(agentId)}`, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<AgentProfile>(response);
}

/**
 * Get listings for a specific agent (public endpoint).
 */
export async function getAgentListings(
  agentId: string,
  params?: { listing_type?: 'sale' | 'rent'; page?: number; page_size?: number }
): Promise<AgentListingListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.listing_type) searchParams.append('listing_type', params.listing_type);
  if (params?.page) searchParams.append('page', String(params.page));
  if (params?.page_size) searchParams.append('page_size', String(params.page_size));

  const queryString = searchParams.toString();
  const url = queryString
    ? `${getApiUrl()}/agents/${encodeURIComponent(agentId)}/listings?${queryString}`
    : `${getApiUrl()}/agents/${encodeURIComponent(agentId)}/listings`;

  const response = await safeFetch(url, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<AgentListingListResponse>(response);
}

/**
 * Send an inquiry to an agent (public endpoint).
 */
export async function contactAgent(
  agentId: string,
  data: AgentInquiryCreate
): Promise<AgentInquiry> {
  const response = await safeFetch(`${getApiUrl()}/agents/${encodeURIComponent(agentId)}/contact`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(data),
  });
  return handleResponse<AgentInquiry>(response);
}

/**
 * Schedule a viewing appointment with an agent (public endpoint).
 */
export async function scheduleViewing(
  agentId: string,
  data: ViewingAppointmentCreate
): Promise<ViewingAppointment> {
  const response = await safeFetch(
    `${getApiUrl()}/agents/${encodeURIComponent(agentId)}/schedule-viewing`,
    {
      method: 'POST',
      headers: buildHeaders(),
      credentials: 'include',
      body: JSON.stringify(data),
    }
  );
  return handleResponse<ViewingAppointment>(response);
}

/**
 * Get current agent's own profile (protected - requires agent role).
 */
export async function getOwnAgentProfile(): Promise<AgentProfile | null> {
  const response = await safeFetch(`${getApiUrl()}/agents/profile`, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<AgentProfile | null>(response);
}

/**
 * Create agent profile (protected - requires agent role).
 */
export async function createAgentProfile(data: AgentProfileCreate): Promise<AgentProfile> {
  const response = await safeFetch(`${getApiUrl()}/agents/profile`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(data),
  });
  return handleResponse<AgentProfile>(response);
}

/**
 * Update current agent's profile (protected - requires agent role).
 */
export async function updateOwnAgentProfile(data: AgentProfileUpdate): Promise<AgentProfile> {
  const response = await safeFetch(`${getApiUrl()}/agents/profile`, {
    method: 'PATCH',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(data),
  });
  return handleResponse<AgentProfile>(response);
}

/**
 * Get inquiries for current agent (protected - requires agent role).
 */
export async function getOwnInquiries(params?: {
  status?: 'new' | 'read' | 'responded' | 'closed';
  page?: number;
  page_size?: number;
}): Promise<AgentInquiryListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.append('status', params.status);
  if (params?.page) searchParams.append('page', String(params.page));
  if (params?.page_size) searchParams.append('page_size', String(params.page_size));

  const queryString = searchParams.toString();
  const url = queryString
    ? `${getApiUrl()}/agents/inquiries?${queryString}`
    : `${getApiUrl()}/agents/inquiries`;

  const response = await safeFetch(url, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<AgentInquiryListResponse>(response);
}

/**
 * Update an inquiry (protected - requires agent role).
 */
export async function updateInquiry(
  inquiryId: string,
  data: AgentInquiryUpdate
): Promise<AgentInquiry> {
  const response = await safeFetch(
    `${getApiUrl()}/agents/inquiries/${encodeURIComponent(inquiryId)}`,
    {
      method: 'PATCH',
      headers: buildHeaders(),
      credentials: 'include',
      body: JSON.stringify(data),
    }
  );
  return handleResponse<AgentInquiry>(response);
}

/**
 * Get appointments for current agent (protected - requires agent role).
 */
export async function getOwnAppointments(params?: {
  status?: 'requested' | 'confirmed' | 'cancelled' | 'completed';
  page?: number;
  page_size?: number;
}): Promise<ViewingAppointmentListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.append('status', params.status);
  if (params?.page) searchParams.append('page', String(params.page));
  if (params?.page_size) searchParams.append('page_size', String(params.page_size));

  const queryString = searchParams.toString();
  const url = queryString
    ? `${getApiUrl()}/agents/appointments?${queryString}`
    : `${getApiUrl()}/agents/appointments`;

  const response = await safeFetch(url, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<ViewingAppointmentListResponse>(response);
}

/**
 * Update an appointment (protected - requires agent role).
 */
export async function updateAppointment(
  appointmentId: string,
  data: ViewingAppointmentUpdate
): Promise<ViewingAppointment> {
  const response = await safeFetch(
    `${getApiUrl()}/agents/appointments/${encodeURIComponent(appointmentId)}`,
    {
      method: 'PATCH',
      headers: buildHeaders(),
      credentials: 'include',
      body: JSON.stringify(data),
    }
  );
  return handleResponse<ViewingAppointment>(response);
}

// =============================================================================
// Document Management API (Task #43)
// =============================================================================

/**
 * Upload a document file.
 */
export async function uploadDocument(
  file: File,
  metadata?: {
    property_id?: string;
    category?: string;
    tags?: string[];
    description?: string;
    expiry_date?: string;
  }
): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (metadata?.property_id) formData.append('property_id', metadata.property_id);
  if (metadata?.category) formData.append('category', metadata.category);
  if (metadata?.tags) formData.append('tags', JSON.stringify(metadata.tags));
  if (metadata?.description) formData.append('description', metadata.description);
  if (metadata?.expiry_date) formData.append('expiry_date', metadata.expiry_date);

  const response = await safeFetch(`${getApiUrl()}/documents`, {
    method: 'POST',
    headers: buildMultipartHeaders(),
    credentials: 'include',
    body: formData,
  });
  return handleResponse<DocumentUploadResponse>(response);
}

/**
 * List documents with optional filters.
 */
export async function getDocuments(params?: {
  property_id?: string;
  category?: string;
  ocr_status?: string;
  search_query?: string;
  sort_by?: string;
  sort_order?: string;
  page?: number;
  page_size?: number;
}): Promise<DocumentListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.property_id) searchParams.append('property_id', params.property_id);
  if (params?.category) searchParams.append('category', params.category);
  if (params?.ocr_status) searchParams.append('ocr_status', params.ocr_status);
  if (params?.search_query) searchParams.append('search_query', params.search_query);
  if (params?.sort_by) searchParams.append('sort_by', params.sort_by);
  if (params?.sort_order) searchParams.append('sort_order', params.sort_order);
  if (params?.page) searchParams.append('page', String(params.page));
  if (params?.page_size) searchParams.append('page_size', String(params.page_size));

  const queryString = searchParams.toString();
  const url = queryString ? `${getApiUrl()}/documents?${queryString}` : `${getApiUrl()}/documents`;

  const response = await safeFetch(url, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<DocumentListResponse>(response);
}

/**
 * Get expiring documents.
 */
export async function getExpiringDocuments(
  daysAhead: number = 30
): Promise<ExpiringDocumentsResponse> {
  const response = await safeFetch(`${getApiUrl()}/documents/expiring?days_ahead=${daysAhead}`, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  return handleResponse<ExpiringDocumentsResponse>(response);
}

/**
 * Get document download URL.
 */
export function getDocumentDownloadUrl(documentId: string): string {
  return `${getApiUrl()}/documents/${encodeURIComponent(documentId)}`;
}

/**
 * Update document metadata.
 */
export async function updateDocument(
  documentId: string,
  data: DocumentUpdateRequest
): Promise<Document> {
  const response = await safeFetch(`${getApiUrl()}/documents/${encodeURIComponent(documentId)}`, {
    method: 'PATCH',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(data),
  });
  return handleResponse<Document>(response);
}

/**
 * Delete a document.
 */
export async function deleteDocument(documentId: string): Promise<void> {
  const response = await safeFetch(`${getApiUrl()}/documents/${encodeURIComponent(documentId)}`, {
    method: 'DELETE',
    headers: buildHeaders(),
    credentials: 'include',
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(error.detail || 'Failed to delete document', response.status);
  }
}

// =============================================================================
// E-Signature API Functions (Task #57)
// =============================================================================

/**
 * Create a signature request
 */
export async function createSignatureRequest(
  data: SignatureRequestCreate
): Promise<SignatureRequest> {
  const response = await fetch(`${getApiUrl()}/signatures/request`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(error.detail || 'Failed to create signature request', response.status);
  }
  return response.json();
}

/**
 * Get signature requests with optional filters
 */
export async function getSignatureRequests(
  filters?: SignatureRequestFilters
): Promise<SignatureRequestListResponse> {
  const params = new URLSearchParams();
  if (filters?.status) params.append('status', filters.status);
  if (filters?.property_id) params.append('property_id', filters.property_id);
  if (filters?.page) params.append('page', filters.page.toString());
  if (filters?.page_size) params.append('page_size', filters.page_size.toString());
  if (filters?.sort_by) params.append('sort_by', filters.sort_by);
  if (filters?.sort_order) params.append('sort_order', filters.sort_order);

  const response = await fetch(`${getApiUrl()}/signatures?${params.toString()}`, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(error.detail || 'Failed to get signature requests', response.status);
  }
  return response.json();
}

/**
 * Get a single signature request by ID
 */
export async function getSignatureRequest(id: string): Promise<SignatureRequest> {
  const response = await fetch(`${getApiUrl()}/signatures/${id}`, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(error.detail || 'Failed to get signature request', response.status);
  }
  return response.json();
}

/**
 * Cancel a signature request
 */
export async function cancelSignatureRequest(
  id: string
): Promise<{ status: string; request_id: string }> {
  const response = await fetch(`${getApiUrl()}/signatures/${id}/cancel`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(error.detail || 'Failed to cancel signature request', response.status);
  }
  return response.json();
}

/**
 * Send a reminder to pending signers
 */
export async function sendSignatureReminder(
  id: string
): Promise<{ status: string; request_id: string }> {
  const response = await fetch(`${getApiUrl()}/signatures/${id}/reminder`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(error.detail || 'Failed to send reminder', response.status);
  }
  return response.json();
}

/**
 * Get the download URL for a signed document
 */
export function getSignedDocumentDownloadUrl(requestId: string): string {
  return `${getApiUrl()}/signatures/${requestId}/download`;
}

// =============================================================================
// Document Template API Functions (Task #57)
// =============================================================================

/**
 * Get document templates with optional filters
 */
export async function getDocumentTemplates(filters?: {
  template_type?: string;
  page?: number;
  page_size?: number;
}): Promise<DocumentTemplateListResponse> {
  const params = new URLSearchParams();
  if (filters?.template_type) params.append('template_type', filters.template_type);
  if (filters?.page) params.append('page', filters.page.toString());
  if (filters?.page_size) params.append('page_size', filters.page_size.toString());

  const response = await fetch(`${getApiUrl()}/signatures/templates?${params.toString()}`, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(error.detail || 'Failed to get templates', response.status);
  }
  return response.json();
}

/**
 * Get a single document template by ID
 */
export async function getDocumentTemplate(id: string): Promise<DocumentTemplate> {
  const response = await fetch(`${getApiUrl()}/signatures/templates/${id}`, {
    method: 'GET',
    headers: buildHeaders(),
    credentials: 'include',
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(error.detail || 'Failed to get template', response.status);
  }
  return response.json();
}

/**
 * Create a new document template
 */
export async function createDocumentTemplate(
  data: DocumentTemplateCreate
): Promise<DocumentTemplate> {
  const response = await fetch(`${getApiUrl()}/signatures/templates`, {
    method: 'POST',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(error.detail || 'Failed to create template', response.status);
  }
  return response.json();
}

/**
 * Update an existing document template
 */
export async function updateDocumentTemplate(
  id: string,
  data: DocumentTemplateUpdate
): Promise<DocumentTemplate> {
  const response = await fetch(`${getApiUrl()}/signatures/templates/${id}`, {
    method: 'PUT',
    headers: buildHeaders(),
    credentials: 'include',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(error.detail || 'Failed to update template', response.status);
  }
  return response.json();
}

/**
 * Delete a document template
 */
export async function deleteDocumentTemplate(id: string): Promise<void> {
  const response = await fetch(`${getApiUrl()}/signatures/templates/${id}`, {
    method: 'DELETE',
    headers: buildHeaders(),
    credentials: 'include',
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(error.detail || 'Failed to delete template', response.status);
  }
}
