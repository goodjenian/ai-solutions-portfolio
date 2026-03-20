'use client';

import { useState, useEffect } from 'react';
import {
  FileUp,
  Loader2,
  Upload,
  AlertCircle,
  FileSpreadsheet,
  CheckCircle2,
  Table,
  Database,
  Globe,
  Filter,
} from 'lucide-react';
import { ingestData, getExcelSheets, listPortals, fetchFromPortal, ingestFileUpload, getExcelSheetsUpload, ApiError } from '@/lib/api';
import type { IngestResponse, PortalAdapterInfo } from '@/lib/types';

interface ErrorState {
  message: string;
  requestId?: string;
}

interface SheetInfo {
  name: string;
  rowCount: number;
}

type TabType = 'url' | 'portal';

export default function DataSourcesPage() {
  const [activeTab, setActiveTab] = useState<TabType>('url');
  const [fileUrl, setFileUrl] = useState<string>('');
  const [sourceName, setSourceName] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ErrorState | null>(null);
  const [result, setResult] = useState<IngestResponse | null>(null);

  // Excel sheets state
  const [loadingSheets, setLoadingSheets] = useState(false);
  const [sheets, setSheets] = useState<SheetInfo[]>([]);
  const [selectedSheet, setSelectedSheet] = useState<string>('');
  const [headerRow, setHeaderRow] = useState<number>(0);

  // File upload state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadMode, setUploadMode] = useState<'url' | 'file'>('url');

  // Portal state
  const [portals, setPortals] = useState<PortalAdapterInfo[]>([]);
  const [loadingPortals, setLoadingPortals] = useState(true);
  const [selectedPortal, setSelectedPortal] = useState<string>('');
  const [portalCity, setPortalCity] = useState<string>('');
  const [portalMinPrice, setPortalMinPrice] = useState<string>('');
  const [portalMaxPrice, setPortalMaxPrice] = useState<string>('');
  const [portalMinRooms, setPortalMinRooms] = useState<string>('');
  const [portalMaxRooms, setPortalMaxRooms] = useState<string>('');
  const [portalPropertyType, setPortalPropertyType] = useState<string>('');
  const [portalListingType, setPortalListingType] = useState<string>('rent');
  const [portalLimit, setPortalLimit] = useState<number>(50);

  // Load available portals on mount
  useEffect(() => {
    listPortals()
      .then((data) => {
        setPortals(data.adapters);
        if (data.adapters.length > 0) {
          setSelectedPortal(data.adapters[0].name);
        }
      })
      .catch((e: unknown) => {
        console.error('Failed to load portals:', e);
      })
      .finally(() => {
        setLoadingPortals(false);
      });
  }, []);

  const isExcelFile = (url: string): boolean => {
    const lowerUrl = url.toLowerCase();
    return lowerUrl.endsWith('.xlsx') || lowerUrl.endsWith('.xls') || lowerUrl.endsWith('.ods');
  };

  const isExcelFileObj = (file: File | null): boolean => {
    if (!file) return false;
    const name = file.name.toLowerCase();
    return name.endsWith('.xlsx') || name.endsWith('.xls') || name.endsWith('.ods');
  };

  const extractErrorState = (err: unknown): ErrorState => {
    let message = 'Unknown error';
    let requestId: string | undefined = undefined;

    if (err instanceof ApiError) {
      message = err.message;
      requestId = err.request_id;
    } else if (err instanceof Error) {
      message = err.message;
    } else {
      message = String(err);
    }

    return { message, requestId };
  };

  const onLoadSheets = async () => {
    const url = fileUrl.trim();
    if (!url) {
      setError({ message: 'Please enter a file URL first.' });
      return;
    }

    if (!isExcelFile(url)) {
      setError({
        message: 'URL must point to an Excel file (.xlsx, .xls, or .ods).',
      });
      return;
    }

    setLoadingSheets(true);
    setError(null);
    setSheets([]);

    try {
      const res = await getExcelSheets({ file_url: url });
      const sheetInfo: SheetInfo[] = res.sheet_names.map((name) => ({
        name,
        rowCount: res.row_count[name] || 0,
      }));
      setSheets(sheetInfo);
      if (res.default_sheet) {
        setSelectedSheet(res.default_sheet);
      }
    } catch (e: unknown) {
      setError(extractErrorState(e));
    } finally {
      setLoadingSheets(false);
    }
  };

  const onLoadSheetsUpload = async () => {
    if (!uploadFile) {
      setError({ message: 'Please select a file first.' });
      return;
    }

    if (!isExcelFileObj(uploadFile)) {
      setError({
        message: 'File must be an Excel file (.xlsx, .xls, or .ods).',
      });
      return;
    }

    setLoadingSheets(true);
    setError(null);
    setSheets([]);

    try {
      const res = await getExcelSheetsUpload(uploadFile);
      const sheetInfo: SheetInfo[] = res.sheet_names.map((name) => ({
        name,
        rowCount: res.row_count[name] || 0,
      }));
      setSheets(sheetInfo);
      if (res.default_sheet) {
        setSelectedSheet(res.default_sheet);
      }
    } catch (e: unknown) {
      setError(extractErrorState(e));
    } finally {
      setLoadingSheets(false);
    }
  };

  const onIngest = async () => {
    // File upload mode
    if (uploadMode === 'file') {
      if (!uploadFile) {
        setError({ message: 'Please select a file to upload.' });
        return;
      }

      setLoading(true);
      setError(null);
      setResult(null);

      try {
        const res = await ingestFileUpload(uploadFile, {
          sheet_name: isExcelFileObj(uploadFile) ? selectedSheet || undefined : undefined,
          header_row: headerRow,
          source_name: sourceName.trim() || undefined,
        });
        setResult(res);
      } catch (e: unknown) {
        setError(extractErrorState(e));
      } finally {
        setLoading(false);
      }
      return;
    }

    // URL mode
    const url = fileUrl.trim();
    if (!url) {
      setError({ message: 'Please enter a file URL.' });
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const request = {
        file_urls: [url],
        sheet_name: isExcelFile(url) ? selectedSheet || undefined : undefined,
        header_row: headerRow,
        source_name: sourceName.trim() || undefined,
      };
      const res = await ingestData(request);
      setResult(res);
    } catch (e: unknown) {
      setError(extractErrorState(e));
    } finally {
      setLoading(false);
    }
  };

  const onFetchFromPortal = async () => {
    if (!selectedPortal) {
      setError({ message: 'Please select a portal.' });
      return;
    }

    if (!portalCity.trim()) {
      setError({ message: 'Please enter a city.' });
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const request = {
        portal: selectedPortal,
        city: portalCity.trim(),
        min_price: portalMinPrice ? parseFloat(portalMinPrice) : undefined,
        max_price: portalMaxPrice ? parseFloat(portalMaxPrice) : undefined,
        min_rooms: portalMinRooms ? parseFloat(portalMinRooms) : undefined,
        max_rooms: portalMaxRooms ? parseFloat(portalMaxRooms) : undefined,
        property_type: portalPropertyType || undefined,
        listing_type: portalListingType,
        limit: portalLimit,
        source_name: sourceName.trim() || undefined,
      };
      const res = await fetchFromPortal(request);
      setResult({
        message: res.message,
        properties_processed: res.properties_processed,
        errors: res.errors,
        source_type: res.source_type,
        source_name: res.source_name,
      });
    } catch (e: unknown) {
      setError(extractErrorState(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <div className="flex flex-col space-y-2 mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Data Sources</h1>
        <p className="text-muted-foreground">
          Import property data from files or external portals.
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-4 border-b-2 mb-6">
        <button
          type="button"
          className={`pb-3 px-4 font-medium transition-colors ${
            activeTab === 'url'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('url')}
        >
          <FileUp className="w-4 h-4 inline mr-2" />
          File / URL
        </button>
        <button
          type="button"
          className={`pb-3 px-4 font-medium transition-colors ${
            activeTab === 'portal'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('portal')}
        >
          <Globe className="w-4 h-4 inline mr-2" />
          Portal API
        </button>
      </div>

      {/* File/URL Tab Content */}
      {activeTab === 'url' && (
        <section className="border rounded-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <Database className="w-5 h-5" />
            <h2 className="text-xl font-semibold">Import Data</h2>
          </div>

          {/* Upload Mode Toggle */}
          <div className="flex gap-2 mb-4">
            <button
              type="button"
              className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                uploadMode === 'url'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
              }`}
              onClick={() => {
                setUploadMode('url');
                setSheets([]);
                setSelectedSheet('');
              }}
            >
              <Globe className="w-4 h-4 inline mr-2" />
              From URL
            </button>
            <button
              type="button"
              className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                uploadMode === 'file'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
              }`}
              onClick={() => {
                setUploadMode('file');
                setSheets([]);
                setSelectedSheet('');
              }}
            >
              <Upload className="w-4 h-4 inline mr-2" />
              Upload File
            </button>
          </div>

          <div className="space-y-4">
            {/* URL Input */}
            {uploadMode === 'url' && (
              <div>
                <label htmlFor="fileUrl" className="block text-sm font-medium mb-2">
                  File URL
                </label>
                <input
                  id="fileUrl"
                  className="border p-2 w-full rounded"
                  type="text"
                  placeholder="https://example.com/data.xlsx"
                  value={fileUrl}
                  onChange={(e) => setFileUrl(e.target.value)}
                  disabled={loading}
                  aria-label="File URL"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Supports CSV (.csv) and Excel (.xlsx, .xls, .ods) files
                </p>
              </div>
            )}

            {/* File Upload Input */}
            {uploadMode === 'file' && (
              <div>
                <label htmlFor="fileUpload" className="block text-sm font-medium mb-2">
                  Select File
                </label>
                <input
                  id="fileUpload"
                  className="border p-2 w-full rounded"
                  type="file"
                  accept=".xlsx,.xls,.ods,.csv"
                  onChange={(e) => {
                    setUploadFile(e.target.files?.[0] || null);
                    setSheets([]);
                    setSelectedSheet('');
                  }}
                  disabled={loading}
                  aria-label="File Upload"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Max file size: 25MB. Supports: .xlsx, .xls, .ods, .csv
                </p>
                {uploadFile && (
                  <p className="text-sm text-muted-foreground mt-2">
                    Selected: <strong>{uploadFile.name}</strong> ({(uploadFile.size / 1024 / 1024).toFixed(2)} MB)
                  </p>
                )}
              </div>
            )}

            <div>
              <label htmlFor="sourceName" className="block text-sm font-medium mb-2">
                Source Name (optional)
              </label>
              <input
                id="sourceName"
                className="border p-2 w-full rounded"
                type="text"
                placeholder="e.g., Q1 2024 Properties"
                value={sourceName}
                onChange={(e) => setSourceName(e.target.value)}
                disabled={loading}
                aria-label="Source Name"
              />
            </div>

            {/* Excel-specific options */}
            {((uploadMode === 'url' && isExcelFile(fileUrl)) || (uploadMode === 'file' && isExcelFileObj(uploadFile))) && (
              <div className="border-t pt-4 mt-4">
                <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                  <FileSpreadsheet className="w-4 h-4" />
                  Excel Options
                </h3>

                <div className="grid gap-4">
                  <div className="flex gap-2">
                    <button
                      type="button"
                      className="px-4 py-2 bg-secondary text-secondary-foreground rounded hover:bg-secondary/80 disabled:opacity-50"
                      onClick={uploadMode === 'url' ? onLoadSheets : onLoadSheetsUpload}
                      disabled={loadingSheets || loading}
                    >
                      {loadingSheets ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Loading sheets...
                        </>
                      ) : (
                        <>
                          <Table className="w-4 h-4 mr-2" />
                          Load Sheets
                        </>
                      )}
                    </button>
                  </div>

                  {sheets.length > 0 && (
                    <>
                      <div>
                        <label htmlFor="sheetSelect" className="block text-sm font-medium mb-2">
                          Select Sheet
                        </label>
                        <select
                          id="sheetSelect"
                          className="border p-2 w-full rounded"
                          value={selectedSheet}
                          onChange={(e) => setSelectedSheet(e.target.value)}
                          disabled={loading}
                        >
                          {sheets.map((sheet) => (
                            <option key={sheet.name} value={sheet.name}>
                              {sheet.name} ({sheet.rowCount} rows)
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label htmlFor="headerRow" className="block text-sm font-medium mb-2">
                          Header Row (0-indexed)
                        </label>
                        <input
                          id="headerRow"
                          className="border p-2 w-full rounded"
                          type="number"
                          min="0"
                          value={headerRow}
                          onChange={(e) => setHeaderRow(parseInt(e.target.value) || 0)}
                          disabled={loading}
                        />
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            <button
              type="button"
              className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
              onClick={onIngest}
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Importing...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Import Data
                </>
              )}
            </button>
          </div>
        </section>
      )}

      {/* Portal Tab Content */}
      {activeTab === 'portal' && (
        <section className="border rounded-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <Globe className="w-5 h-5" />
            <h2 className="text-xl font-semibold">Fetch from Portal</h2>
          </div>

          {loadingPortals ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin mr-2" />
              Loading available portals...
            </div>
          ) : portals.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No portal adapters available. Configure adapters in the backend.
            </div>
          ) : (
            <div className="space-y-4">
              {/* Portal selector */}
              <div>
                <label htmlFor="portalSelect" className="block text-sm font-medium mb-2">
                  Portal
                </label>
                <select
                  id="portalSelect"
                  className="border p-2 w-full rounded"
                  value={selectedPortal}
                  onChange={(e) => setSelectedPortal(e.target.value)}
                  disabled={loading}
                >
                  {portals.map((portal) => (
                    <option key={portal.name} value={portal.name} disabled={!portal.configured}>
                      {portal.display_name}
                      {!portal.configured && ' (not configured)'}
                    </option>
                  ))}
                </select>
              </div>

              {/* Required: City */}
              <div>
                <label htmlFor="portalCity" className="block text-sm font-medium mb-2">
                  City * (required)
                </label>
                <input
                  id="portalCity"
                  className="border p-2 w-full rounded"
                  type="text"
                  placeholder="e.g., Warsaw"
                  value={portalCity}
                  onChange={(e) => setPortalCity(e.target.value)}
                  disabled={loading}
                  aria-label="City"
                />
              </div>

              {/* Optional filters */}
              <div className="border-t pt-4 mt-4">
                <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                  <Filter className="w-4 h-4" />
                  Filters (optional)
                </h3>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="minPrice" className="block text-sm font-medium mb-2">
                      Min Price
                    </label>
                    <input
                      id="minPrice"
                      className="border p-2 w-full rounded"
                      type="number"
                      min="0"
                      step="100"
                      placeholder="e.g., 1000"
                      value={portalMinPrice}
                      onChange={(e) => setPortalMinPrice(e.target.value)}
                      disabled={loading}
                    />
                  </div>

                  <div>
                    <label htmlFor="maxPrice" className="block text-sm font-medium mb-2">
                      Max Price
                    </label>
                    <input
                      id="maxPrice"
                      className="border p-2 w-full rounded"
                      type="number"
                      min="0"
                      step="100"
                      placeholder="e.g., 5000"
                      value={portalMaxPrice}
                      onChange={(e) => setPortalMaxPrice(e.target.value)}
                      disabled={loading}
                    />
                  </div>

                  <div>
                    <label htmlFor="minRooms" className="block text-sm font-medium mb-2">
                      Min Rooms
                    </label>
                    <input
                      id="minRooms"
                      className="border p-2 w-full rounded"
                      type="number"
                      min="0"
                      step="0.5"
                      placeholder="e.g., 1"
                      value={portalMinRooms}
                      onChange={(e) => setPortalMinRooms(e.target.value)}
                      disabled={loading}
                    />
                  </div>

                  <div>
                    <label htmlFor="maxRooms" className="block text-sm font-medium mb-2">
                      Max Rooms
                    </label>
                    <input
                      id="maxRooms"
                      className="border p-2 w-full rounded"
                      type="number"
                      min="0"
                      step="0.5"
                      placeholder="e.g., 4"
                      value={portalMaxRooms}
                      onChange={(e) => setPortalMaxRooms(e.target.value)}
                      disabled={loading}
                    />
                  </div>

                  <div>
                    <label htmlFor="propertyType" className="block text-sm font-medium mb-2">
                      Property Type
                    </label>
                    <select
                      id="propertyType"
                      className="border p-2 w-full rounded"
                      value={portalPropertyType}
                      onChange={(e) => setPortalPropertyType(e.target.value)}
                      disabled={loading}
                    >
                      <option value="">Any</option>
                      <option value="apartment">Apartment</option>
                      <option value="house">House</option>
                      <option value="studio">Studio</option>
                    </select>
                  </div>

                  <div>
                    <label htmlFor="listingType" className="block text-sm font-medium mb-2">
                      Listing Type
                    </label>
                    <select
                      id="listingType"
                      className="border p-2 w-full rounded"
                      value={portalListingType}
                      onChange={(e) => setPortalListingType(e.target.value)}
                      disabled={loading}
                    >
                      <option value="rent">Rent</option>
                      <option value="sale">Sale</option>
                    </select>
                  </div>
                </div>

                <div className="mt-4">
                  <label htmlFor="limit" className="block text-sm font-medium mb-2">
                    Max Results
                  </label>
                  <input
                    id="limit"
                    className="border p-2 w-full rounded"
                    type="number"
                    min="1"
                    max="500"
                    value={portalLimit}
                    onChange={(e) => setPortalLimit(parseInt(e.target.value) || 50)}
                    disabled={loading}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="portalSourceName" className="block text-sm font-medium mb-2">
                  Source Name (optional)
                </label>
                <input
                  id="portalSourceName"
                  className="border p-2 w-full rounded"
                  type="text"
                  placeholder="e.g., Warsaw Rentals"
                  value={sourceName}
                  onChange={(e) => setSourceName(e.target.value)}
                  disabled={loading}
                  aria-label="Source Name"
                />
              </div>

              <button
                type="button"
                className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
                onClick={onFetchFromPortal}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Fetching...
                  </>
                ) : (
                  <>
                    <Globe className="w-4 h-4" />
                    Fetch from Portal
                  </>
                )}
              </button>
            </div>
          )}
        </section>
      )}

      {/* Error Display */}
      {error && (
        <div className="flex items-start gap-3 p-4 bg-destructive/10 text-destructive rounded mt-4">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Error</p>
            <p className="text-sm">{error.message}</p>
            {error.requestId && <p className="text-xs mt-1">Request ID: {error.requestId}</p>}
          </div>
        </div>
      )}

      {/* Success Display */}
      {result && (
        <div className="flex items-start gap-3 p-4 bg-green-50 text-green-900 dark:bg-green-950 dark:text-green-100 rounded mt-4">
          <CheckCircle2 className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Import Successful</p>
            <p className="text-sm">{result.message}</p>
            <p className="text-xs mt-1">Properties processed: {result.properties_processed}</p>
            {result.source_type && <p className="text-xs">Source type: {result.source_type}</p>}
            {result.source_name && <p className="text-xs">Source name: {result.source_name}</p>}
            {result.errors.length > 0 && (
              <details className="mt-2">
                <summary className="text-xs cursor-pointer">
                  Warnings ({result.errors.length})
                </summary>
                <ul className="text-xs mt-1 list-disc list-inside">
                  {result.errors.map((err, i) => (
                    <li key={i}>{err}</li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        </div>
      )}

      {/* Info Section */}
      <section className="border rounded-lg p-6 bg-muted/50 mt-8">
        <div className="flex items-center gap-2 mb-4">
          <FileUp className="w-5 h-5" />
          <h2 className="text-xl font-semibold">Supported Data Sources</h2>
        </div>
        <div className="space-y-2 text-sm">
          <p>
            <strong>CSV:</strong> Comma-separated values file
          </p>
          <p>
            <strong>Excel (.xlsx):</strong> Modern Excel format with openpyxl
          </p>
          <p>
            <strong>Excel (.xls):</strong> Legacy Excel format with xlrd
          </p>
          <p>
            <strong>ODF Spreadsheet (.ods):</strong> OpenDocument format with odfpy
          </p>
          <p>
            <strong>Portals:</strong> External APIs (OpenStreetMap/Overpass available)
          </p>
        </div>
      </section>
    </div>
  );
}
