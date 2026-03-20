from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

from data.schemas import Property
from utils.exporters import ExportFormat


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class SortField(str, Enum):
    RELEVANCE = "relevance"
    PRICE = "price"
    PRICE_PER_SQM = "price_per_sqm"
    AREA = "area_sqm"
    YEAR_BUILT = "year_built"


class HealthCheck(BaseModel):
    """Health check response model."""

    status: str
    version: str


class AdminVersionInfo(BaseModel):
    version: str
    environment: str
    app_title: str
    python_version: str
    platform: str


class NotificationsAdminStats(BaseModel):
    scheduler_running: bool
    alerts_storage_path: str

    sent_alerts_total: int
    pending_alerts_total: int
    pending_alerts_by_type: Dict[str, int] = Field(default_factory=dict)
    pending_alerts_oldest_created_at: Optional[datetime] = None
    pending_alerts_newest_created_at: Optional[datetime] = None


class SearchRequest(BaseModel):
    """Search request model."""

    query: str
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None
    alpha: float = 0.7

    # Geospatial
    lat: Optional[float] = Field(None, ge=-90, le=90, description="Latitude for geo-search")
    lon: Optional[float] = Field(None, ge=-180, le=180, description="Longitude for geo-search")
    radius_km: Optional[float] = Field(None, gt=0, description="Radius in kilometers")
    min_lat: Optional[float] = Field(None, ge=-90, le=90, description="Bounding box min latitude")
    max_lat: Optional[float] = Field(None, ge=-90, le=90, description="Bounding box max latitude")
    min_lon: Optional[float] = Field(
        None, ge=-180, le=180, description="Bounding box min longitude"
    )
    max_lon: Optional[float] = Field(
        None, ge=-180, le=180, description="Bounding box max longitude"
    )

    # Polygon filter for drawn areas (GeoJSON polygon coordinates)
    polygon: Optional[List[List[float]]] = Field(
        None,
        description="GeoJSON polygon coordinates for geo-search (list of [lon, lat] pairs)",
    )

    # Sorting
    sort_by: Optional[SortField] = SortField.RELEVANCE
    sort_order: Optional[SortOrder] = SortOrder.DESC


class SearchResultItem(BaseModel):
    """Search result item with score."""

    property: Property
    score: float


class SearchResponse(BaseModel):
    """Search response model."""

    results: List[SearchResultItem]
    count: int


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str
    session_id: Optional[str] = None
    stream: bool = False
    include_intermediate_steps: bool = False


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str
    sources: List[Dict[str, Any]] = []
    sources_truncated: bool = False
    session_id: Optional[str] = None
    intermediate_steps: Optional[List[Dict[str, Any]]] = None


class RagCitation(BaseModel):
    source: Optional[str] = None
    chunk_index: Optional[int] = None
    page_number: Optional[int] = None
    paragraph_number: Optional[int] = None


class RagQaRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=50)
    provider: Optional[str] = None
    model: Optional[str] = None


class RagQaResponse(BaseModel):
    answer: str
    citations: List[RagCitation] = Field(default_factory=list)
    llm_used: bool = False
    provider: Optional[str] = None
    model: Optional[str] = None


class RagResetResponse(BaseModel):
    message: str
    documents_removed: int
    documents_remaining: int


class IngestRequest(BaseModel):
    """Request model for data ingestion."""

    file_urls: Optional[List[str]] = None
    force: bool = False
    # Excel-specific options
    sheet_name: Optional[str] = Field(
        None, description="Excel sheet name to load (for .xlsx, .xls, .ods files)"
    )
    header_row: Optional[int] = Field(
        0, ge=0, description="Header row number for Excel files (0-indexed)"
    )
    source_name: Optional[str] = Field(
        None, description="Optional source name for tracking (e.g., 'properties_2024_q1')"
    )


class IngestResponse(BaseModel):
    """Response model for data ingestion."""

    message: str
    properties_processed: int
    errors: List[str] = []
    source_type: Optional[str] = None
    source_name: Optional[str] = None


class ExcelSheetsRequest(BaseModel):
    """Request model for getting Excel sheet names."""

    file_url: str = Field(..., description="URL to Excel file")


class ExcelSheetsResponse(BaseModel):
    """Response model for Excel sheet names."""

    file_url: str
    sheet_names: List[str]
    default_sheet: Optional[str] = None
    row_count: Dict[str, int] = Field(default_factory=dict, description="Row count per sheet")


class ReindexRequest(BaseModel):
    """Request model for reindexing."""

    clear_existing: bool = False


class ReindexResponse(BaseModel):
    """Response model for reindexing."""

    message: str
    count: int


class NotificationSettings(BaseModel):
    """User notification settings."""

    email_digest: bool = True
    frequency: str = "weekly"
    expert_mode: bool = False
    marketing_emails: bool = False


class ModelPricing(BaseModel):
    input_price_per_1m: float
    output_price_per_1m: float
    currency: str = "USD"


class ModelCatalogItem(BaseModel):
    id: str
    display_name: str
    provider_name: str
    context_window: int
    pricing: Optional[ModelPricing] = None
    capabilities: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    recommended_for: List[str] = Field(default_factory=list)


class ModelProviderCatalog(BaseModel):
    name: str
    display_name: str
    is_local: bool
    requires_api_key: bool
    models: List[ModelCatalogItem]
    runtime_available: Optional[bool] = None
    available_models: Optional[List[str]] = None
    runtime_error: Optional[str] = None


class ModelRuntimeTestResponse(BaseModel):
    provider: str
    is_local: bool
    runtime_available: Optional[bool] = None
    available_models: Optional[List[str]] = None
    runtime_error: Optional[str] = None


class ModelPreferences(BaseModel):
    preferred_provider: Optional[str] = None
    preferred_model: Optional[str] = None


class ModelPreferencesUpdate(BaseModel):
    preferred_provider: Optional[str] = None
    preferred_model: Optional[str] = None

    @model_validator(mode="after")
    def validate_not_empty(self) -> "ModelPreferencesUpdate":
        if self.preferred_provider is None and self.preferred_model is None:
            raise ValueError(
                "At least one of preferred_provider or preferred_model must be provided"
            )
        return self


class ComparePropertiesRequest(BaseModel):
    property_ids: List[str]


class ComparedProperty(BaseModel):
    id: Optional[str] = None
    price: Optional[float] = None
    price_per_sqm: Optional[float] = None
    city: Optional[str] = None
    rooms: Optional[float] = None
    bathrooms: Optional[float] = None
    area_sqm: Optional[float] = None
    year_built: Optional[int] = None
    property_type: Optional[str] = None


class CompareSummary(BaseModel):
    count: int
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    price_difference: Optional[float] = None


class ComparePropertiesResponse(BaseModel):
    properties: List[ComparedProperty]
    summary: CompareSummary


class PriceAnalysisRequest(BaseModel):
    query: str


class PriceAnalysisResponse(BaseModel):
    query: str
    count: int
    average_price: Optional[float] = None
    median_price: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    average_price_per_sqm: Optional[float] = None
    median_price_per_sqm: Optional[float] = None
    distribution_by_type: Dict[str, int] = {}


class LocationAnalysisRequest(BaseModel):
    property_id: str


class LocationAnalysisResponse(BaseModel):
    property_id: str
    city: Optional[str] = None
    neighborhood: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None


class ValuationRequest(BaseModel):
    property_id: str


class ValuationResponse(BaseModel):
    property_id: str
    estimated_value: float


class LegalCheckRequest(BaseModel):
    text: str


class LegalCheckResponse(BaseModel):
    risks: List[Dict[str, Any]] = []
    score: float = 0.0


class DataEnrichmentRequest(BaseModel):
    address: str


class DataEnrichmentResponse(BaseModel):
    address: str
    data: Dict[str, Any] = {}


class CRMContactRequest(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None


class CRMContactResponse(BaseModel):
    id: str


class ExportPropertiesRequest(BaseModel):
    format: ExportFormat
    property_ids: Optional[List[str]] = None
    search: Optional[SearchRequest] = None

    columns: Optional[List[str]] = None
    include_header: bool = True
    csv_delimiter: str = ","
    csv_decimal: str = "."

    include_summary: bool = True
    include_statistics: bool = True
    include_metadata: bool = True
    pretty: bool = True
    max_properties: Optional[int] = None

    @model_validator(mode="after")
    def validate_input(self) -> "ExportPropertiesRequest":
        if not self.property_ids and self.search is None:
            raise ValueError("Either property_ids or search must be provided")
        if len(self.csv_delimiter) != 1 or self.csv_delimiter in ("\n", "\r"):
            raise ValueError("csv_delimiter must be a single non-newline character")
        if len(self.csv_decimal) != 1 or self.csv_decimal in ("\n", "\r"):
            raise ValueError("csv_decimal must be a single non-newline character")
        return self


class PromptTemplateVariableInfo(BaseModel):
    name: str
    description: str
    required: bool = True
    example: Optional[str] = None


class PromptTemplateInfo(BaseModel):
    id: str
    title: str
    category: str
    description: str
    template_text: str
    variables: List[PromptTemplateVariableInfo]


class PromptTemplateApplyRequest(BaseModel):
    template_id: str
    variables: Dict[str, Any] = Field(default_factory=dict)


class PromptTemplateApplyResponse(BaseModel):
    template_id: str
    rendered_text: str


# SSE Event Models for TASK-003.1
class SSEContentEvent(BaseModel):
    """SSE content chunk event."""

    content: str


class SSEErrorEvent(BaseModel):
    """SSE error event for streaming failures."""

    error: str
    request_id: Optional[str] = None


class SSEMetaEvent(BaseModel):
    """SSE meta event with sources and session info."""

    sources: List[Dict[str, Any]] = Field(default_factory=list)
    sources_truncated: bool = False
    session_id: str
    request_id: Optional[str] = None
    intermediate_steps: Optional[List[Dict[str, Any]]] = None


# Portal/API Integration Models for TASK-006
class PortalFiltersRequest(BaseModel):
    """Request model for portal data fetching with filters."""

    portal: str = Field(..., description="Portal adapter name (e.g., 'otodom', 'idealista')")
    city: Optional[str] = Field(None, description="City to search in")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price filter")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price filter")
    min_rooms: Optional[float] = Field(None, ge=0, description="Minimum number of rooms")
    max_rooms: Optional[float] = Field(None, ge=0, description="Maximum number of rooms")
    property_type: Optional[str] = Field(None, description="Property type (apartment, house, etc.)")
    listing_type: Optional[str] = Field("rent", description="Listing type (rent, sale)")
    limit: int = Field(100, ge=1, le=500, description="Maximum results to fetch")
    source_name: Optional[str] = Field(
        None, description="Optional source name for tracking (e.g., 'warsaw_rentals')"
    )


class PortalIngestResponse(BaseModel):
    """Response model for portal data ingestion."""

    success: bool
    message: str
    portal: str
    properties_processed: int
    source_type: str = "portal"
    source_name: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    filters_applied: Optional[Dict[str, Any]] = None


class PortalAdapterInfo(BaseModel):
    """Information about a portal adapter."""

    name: str
    display_name: str
    configured: bool
    has_api_key: bool = False
    rate_limit: Optional[Dict[str, int]] = None


class PortalAdaptersResponse(BaseModel):
    """Response model for listing available portal adapters."""

    adapters: List[PortalAdapterInfo]
    count: int


# Investment Analysis Models for TASK-019
class InvestmentAnalysisRequest(BaseModel):
    """Request model for investment property analysis."""

    property_price: float = Field(..., gt=0, description="Purchase price of the property")
    monthly_rent: float = Field(..., gt=0, description="Expected monthly rental income")
    down_payment_percent: float = Field(
        default=20.0, ge=0, le=100, description="Down payment percentage"
    )
    closing_costs: float = Field(default=0.0, ge=0, description="Closing costs (one-time)")
    renovation_costs: float = Field(default=0.0, ge=0, description="Renovation costs (one-time)")
    interest_rate: float = Field(default=4.5, ge=0, description="Annual interest rate percentage")
    loan_years: int = Field(default=30, gt=0, le=50, description="Loan term in years")
    property_tax_monthly: float = Field(default=0.0, ge=0, description="Monthly property tax")
    insurance_monthly: float = Field(default=0.0, ge=0, description="Monthly insurance")
    hoa_monthly: float = Field(default=0.0, ge=0, description="Monthly HOA fees")
    maintenance_percent: float = Field(
        default=1.0, ge=0, description="Annual maintenance percentage of property value"
    )
    vacancy_rate: float = Field(default=5.0, ge=0, le=100, description="Vacancy rate percentage")
    management_percent: float = Field(
        default=0.0, ge=0, description="Property management fee percentage of rent"
    )


class InvestmentAnalysisResponse(BaseModel):
    """Response model for investment property analysis."""

    monthly_cash_flow: float
    annual_cash_flow: float
    cash_on_cash_roi: float
    cap_rate: float
    gross_yield: float
    net_yield: float
    total_investment: float
    monthly_income: float
    monthly_expenses: float
    annual_income: float
    annual_expenses: float
    monthly_mortgage: float
    investment_score: float
    score_breakdown: Dict[str, float]


class CompareInvestmentsRequest(BaseModel):
    """Request model for comparing investment properties."""

    property_ids: List[str]


class ComparedInvestmentProperty(BaseModel):
    """Investment comparison data for a single property."""

    property_id: Optional[str] = None
    price: Optional[float] = None
    monthly_rent: Optional[float] = None
    monthly_cash_flow: Optional[float] = None
    cash_on_cash_roi: Optional[float] = None
    cap_rate: Optional[float] = None
    investment_score: Optional[float] = None


class CompareInvestmentsResponse(BaseModel):
    """Response model for investment property comparison."""

    properties: List[ComparedInvestmentProperty]
    summary: Dict[str, Any] = Field(default_factory=dict)


# Neighborhood Quality Index Models for TASK-020
# ============================================================================
# TASK-040: Enhanced Neighborhood Quality Models
# ============================================================================


class FactorDetail(BaseModel):
    """Detailed breakdown for a scoring factor."""

    raw_value: Optional[float] = Field(None, description="Original measurement value")
    unit: str = Field(default="", description="Unit of measurement (e.g., 'count', 'AQI')")
    normalized_score: float = Field(..., ge=0, le=100, description="Normalized score 0-100")
    weight: float = Field(..., ge=0, le=1, description="Weight in overall score")
    weighted_score: float = Field(..., description="Score × weight")
    data_source: str = Field(default="", description="Source of the data")
    confidence: float = Field(default=0.5, ge=0, le=1, description="Data quality confidence 0-1")


class CityComparison(BaseModel):
    """Comparison to city average scores."""

    city_name: str
    city_average_score: float = Field(..., description="City's overall average score")
    percentile: int = Field(..., ge=0, le=100, description="Property's percentile in city")
    better_than: List[str] = Field(
        default_factory=list, description="Factors better than city average"
    )
    worse_than: List[str] = Field(
        default_factory=list, description="Factors worse than city average"
    )
    factor_comparison: Optional[Dict[str, Dict[str, float]]] = Field(
        None, description="Detailed factor-by-factor comparison"
    )


class NearbyPOI(BaseModel):
    """A nearby point of interest."""

    id: str
    name: Optional[str] = None
    type: str
    category: str = Field(..., description="Category: school, amenity, green_space, transport")
    latitude: float
    longitude: float
    distance_m: Optional[float] = Field(None, description="Distance in meters")


class NearbyPOIs(BaseModel):
    """Collection of nearby POIs for map visualization."""

    schools: List[NearbyPOI] = Field(default_factory=list)
    amenities: List[NearbyPOI] = Field(default_factory=list)
    green_spaces: List[NearbyPOI] = Field(default_factory=list)
    transport_stops: List[NearbyPOI] = Field(default_factory=list)
    police_stations: List[NearbyPOI] = Field(default_factory=list)


class NeighborhoodQualityRequest(BaseModel):
    """Request model for neighborhood quality analysis."""

    property_id: str = Field(..., min_length=1, description="Property ID to analyze")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude coordinate")
    city: Optional[str] = Field(None, description="City name for data enrichment")
    neighborhood: Optional[str] = Field(None, description="Neighborhood name")
    custom_weights: Optional[Dict[str, float]] = Field(
        None,
        description="Custom weights for scoring factors (must sum to 1.0)",
    )
    compare_to_city_average: bool = Field(
        True,
        description="Include comparison to city average scores",
    )
    include_pois: bool = Field(
        True,
        description="Include nearby POIs for map visualization",
    )


class NeighborhoodQualityResponse(BaseModel):
    """Response model for neighborhood quality analysis."""

    property_id: str
    overall_score: float = Field(
        ..., ge=0, le=100, description="Overall neighborhood quality score (0-100)"
    )
    # Core factors (existing)
    safety_score: float = Field(..., ge=0, le=100, description="Safety score (0-100)")
    schools_score: float = Field(..., ge=0, le=100, description="Schools score (0-100)")
    amenities_score: float = Field(..., ge=0, le=100, description="Amenities score (0-100)")
    walkability_score: float = Field(..., ge=0, le=100, description="Walkability score (0-100)")
    green_space_score: float = Field(..., ge=0, le=100, description="Green space score (0-100)")
    # New factors (Task #40)
    air_quality_score: Optional[float] = Field(
        None, ge=0, le=100, description="Air quality score (0-100)"
    )
    noise_level_score: Optional[float] = Field(
        None, ge=0, le=100, description="Noise level/quietness score (0-100)"
    )
    public_transport_score: Optional[float] = Field(
        None, ge=0, le=100, description="Public transport accessibility score (0-100)"
    )
    # Detailed breakdown
    score_breakdown: Dict[str, float] = Field(
        default_factory=dict, description="Detailed scoring breakdown with weights"
    )
    factor_details: Optional[Dict[str, FactorDetail]] = Field(
        None, description="Detailed information for each factor"
    )
    # City comparison
    city_comparison: Optional[CityComparison] = Field(
        None, description="Comparison to city average scores"
    )
    # POIs for map
    nearby_pois: Optional[NearbyPOIs] = Field(None, description="Nearby POIs for map visualization")
    # Metadata
    data_sources: List[str] = Field(
        default_factory=list, description="Data sources used for scoring"
    )
    data_freshness: Optional[Dict[str, str]] = Field(
        None, description="Timestamp of data fetch per source"
    )
    # Location
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    city: Optional[str] = None
    neighborhood: Optional[str] = None


# ============================================================================
# TASK-021: Commute Time Analysis Models
# ============================================================================


class CommuteTimeRequest(BaseModel):
    """Request model for commute time analysis."""

    property_id: str = Field(..., min_length=1, description="Property ID to analyze commute from")
    destination_lat: float = Field(..., ge=-90, le=90, description="Destination latitude")
    destination_lon: float = Field(..., ge=-180, le=180, description="Destination longitude")
    mode: str = Field(
        default="transit",
        description="Commute mode: 'driving', 'walking', 'bicycling', or 'transit'",
    )
    destination_name: Optional[str] = Field(
        None, description="Optional destination name for display"
    )
    departure_time: Optional[str] = Field(
        None, description="Optional departure time as ISO string (e.g., '2024-01-15T08:30:00')"
    )


class CommuteTimeResult(BaseModel):
    """Single property commute time result."""

    property_id: str
    origin_lat: float
    origin_lon: float
    destination_lat: float
    destination_lon: float
    destination_name: Optional[str] = None
    duration_seconds: int = Field(..., description="Commute duration in seconds")
    duration_text: str = Field(..., description="Human-readable duration (e.g., '45m')")
    distance_meters: int = Field(..., description="Distance in meters")
    distance_text: str = Field(..., description="Human-readable distance (e.g., '12.5km')")
    mode: str
    polyline: Optional[str] = Field(None, description="Encoded polyline for route visualization")
    arrival_time: Optional[str] = None
    departure_time: Optional[str] = None


class CommuteTimeResponse(BaseModel):
    """Response model for commute time analysis."""

    result: CommuteTimeResult


class CommuteRankingRequest(BaseModel):
    """Request model for commute-based property ranking."""

    property_ids: str = Field(
        ..., min_length=1, description="Comma-separated list of property IDs to rank"
    )
    destination_lat: float = Field(..., ge=-90, le=90, description="Destination latitude")
    destination_lon: float = Field(..., ge=-180, le=180, description="Destination longitude")
    mode: str = Field(
        default="transit",
        description="Commute mode: 'driving', 'walking', 'bicycling', or 'transit'",
    )
    destination_name: Optional[str] = Field(
        None, description="Optional destination name for display"
    )
    departure_time: Optional[str] = Field(
        None, description="Optional departure time as ISO string (e.g., '2024-01-15T08:30:00')"
    )


class CommuteRankingResponse(BaseModel):
    """Response model for commute-based property ranking."""

    destination_name: Optional[str] = None
    destination_lat: float
    destination_lon: float
    mode: str
    rankings: List[CommuteTimeResult]
    count: int = Field(..., description="Number of properties ranked")
    fastest_duration_seconds: Optional[int] = None
    slowest_duration_seconds: Optional[int] = None
