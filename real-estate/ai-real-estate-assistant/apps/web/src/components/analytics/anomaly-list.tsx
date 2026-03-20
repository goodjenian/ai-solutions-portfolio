'use client';

import * as React from 'react';
import { useState, useEffect } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { AlertTriangle, Eye, CheckCircle, Clock, Search } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { AnomalyBadge, AnomalyTypeBadge, getSeverityIcon } from './anomaly-badge';
import type { MarketAnomaly, AnomalyFilterParams, AnomalySeverity, AnomalyType } from '@/lib/types';
import { getAnomalies, dismissAnomaly } from '@/lib/api';
import { cn } from '@/lib/utils';

// Extended filter params with state
interface AnomalyFilters extends AnomalyFilterParams {
  search: string;
}

const severityOptions: AnomalySeverity[] = ['critical', 'high', 'medium', 'low'];

const typeOptions: AnomalyType[] = [
  'price_spike',
  'price_drop',
  'volume_spike',
  'volume_drop',
  'unusual_pattern',
];

export function AnomalyList() {
  const [anomalies, setAnomalies] = useState<MarketAnomaly[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<AnomalyFilters>({
    limit: 20,
    offset: 0,
    severity: undefined,
    anomaly_type: undefined,
    scope_type: undefined,
    scope_id: undefined,
    search: '',
  });

  useEffect(() => {
    const loadAnomalies = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await getAnomalies(filters);
        setAnomalies(response.anomalies);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load anomalies');
      } finally {
        setLoading(false);
      }
    };
    loadAnomalies();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.severity, filters.anomaly_type, filters.scope_type, filters.scope_id]);

  const handleDismiss = async (anomalyId: string) => {
    try {
      await dismissAnomaly(anomalyId);
      setAnomalies((prev) => prev.filter((a) => a.id !== anomalyId));
    } catch (err) {
      console.error('Failed to dismiss anomaly:', err);
    }
  };

  const handleFilterChange = (key: keyof AnomalyFilters, value: string | undefined) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
      offset: 0, // Reset to first page when filter changes
    }));
  };

  const filteredAnomalies = anomalies.filter((a) => {
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      return (
        a.anomaly_type.toLowerCase().includes(searchLower) ||
        a.scope_id.toLowerCase().includes(searchLower) ||
        JSON.stringify(a.context).toLowerCase().includes(searchLower)
      );
    }
    return true;
  });

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return formatDistanceToNow(date, { addSuffix: true });
  };

  const getScopeLabel = (scopeType: string, scopeId: string) => {
    switch (scopeType) {
      case 'property':
        return `Property: ${scopeId}`;
      case 'city':
        return `City: ${scopeId}`;
      case 'district':
        return `District: ${scopeId}`;
      case 'market':
        return `Market: ${scopeId}`;
      case 'region':
        return `Region: ${scopeId}`;
      default:
        return scopeId;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-2xl font-bold tracking-tight">Market Anomalies</h2>
          <Badge variant="secondary">{anomalies.length} total</Badge>
        </div>

        <div className="flex gap-2">
          {/* Search */}
          <div className="relative">
            <input
              type="text"
              placeholder="Search anomalies..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              className="pl-10 pr-4 text-sm text-muted"
            />
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted" />
          </div>

          {/* Severity Filter */}
          <select
            value={filters.severity || ''}
            onChange={(e) =>
              handleFilterChange(
                'severity',
                (e.target.value || undefined) as AnomalySeverity | undefined
              )
            }
            className="rounded-md border bg-background px-3 py-2 text-sm"
          >
            <option value="">All Severities</option>
            {severityOptions.map((s) => (
              <option key={s} value={s}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>

          {/* Type Filter */}
          <select
            value={filters.anomaly_type || ''}
            onChange={(e) =>
              handleFilterChange(
                'anomaly_type',
                (e.target.value || undefined) as AnomalyType | undefined
              )
            }
            className="rounded-md border bg-background px-3 py-2 text-sm"
          >
            <option value="">All Types</option>
            {typeOptions.map((t) => (
              <option key={t} value={t}>
                {t
                  .split('_')
                  .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                  .join(' ')}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex justify-center py-8">
          <div className="animate-pulse flex flex-col items-center gap-2">
            <div className="h-4 w-4 bg-muted rounded-full"></div>
            <p className="text-sm text-muted">Loading anomalies...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4">
          <div className="flex items-center gap-2 text-destructive">
            <AlertTriangle className="h-4 w-4" />
            <p className="text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && filteredAnomalies.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-muted">
          <CheckCircle className="h-8 w-8 text-muted" />
          <p className="text-sm">No anomalies detected</p>
          <p className="text-xs mt-1">Anomalies will appear here when detected by the system.</p>
        </div>
      )}

      {/* Anomaly Cards */}
      {!loading && !error && filteredAnomalies.length > 0 && (
        <div className="grid gap-4 md:grid-cols-1 lg:grid-cols-2">
          {filteredAnomalies.map((anomaly) => (
            <Card key={anomaly.id} className="overflow-hidden transition-all hover:shadow-md">
              <div className="p-4 space-y-3">
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    {React.createElement(getSeverityIcon(anomaly.severity), {
                      className: 'h-4 w-4',
                    })}
                    <AnomalyBadge severity={anomaly.severity} />
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted">
                    <Clock className="h-3 w-3" />
                    <span>{formatTimestamp(anomaly.detected_at)}</span>
                  </div>
                </div>

                {/* Type and Scope */}
                <div className="flex items-center gap-2 mt-2">
                  <AnomalyTypeBadge type={anomaly.anomaly_type} />
                  <span className="text-sm text-muted">
                    {getScopeLabel(anomaly.scope_type, anomaly.scope_id)}
                  </span>
                </div>

                {/* Metric Details */}
                <div className="mt-3 space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted">Metric</span>
                    <span className="font-medium">{anomaly.metric_name}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted">Expected</span>
                    <span className="font-medium">
                      {typeof anomaly.expected_value === 'number'
                        ? anomaly.expected_value.toLocaleString()
                        : anomaly.expected_value}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted">Actual</span>
                    <span
                      className={cn(
                        'font-medium',
                        anomaly.actual_value > anomaly.expected_value
                          ? 'text-red-600'
                          : 'text-green-600'
                      )}
                    >
                      {typeof anomaly.actual_value === 'number'
                        ? anomaly.actual_value.toLocaleString()
                        : anomaly.actual_value}
                    </span>
                  </div>
                </div>

                {/* Deviation */}
                <div className="flex items-center justify-between rounded-md bg-muted/50 p-2">
                  <span className="text-sm font-medium">Deviation</span>
                  <span
                    className={cn(
                      'font-bold',
                      anomaly.deviation_percent > 0
                        ? anomaly.deviation_percent > 50
                          ? 'text-red-600'
                          : anomaly.deviation_percent > 20
                            ? 'text-orange-600'
                            : 'text-yellow-600'
                        : 'text-green-600'
                    )}
                  >
                    {anomaly.deviation_percent > 0 ? '+' : '-'}
                    {Math.abs(anomaly.deviation_percent).toFixed(1)}%
                  </span>
                </div>

                {/* Z-Score (if available) */}
                {anomaly.z_score !== undefined && anomaly.z_score !== null && (
                  <div className="mt-2 flex items-center justify-between text-xs">
                    <span className="text-muted">Z-Score</span>
                    <span
                      className={cn(
                        'font-medium',
                        Math.abs(anomaly.z_score) > 3 ? 'text-red-600' : ''
                      )}
                    >
                      {anomaly.z_score.toFixed(2)}
                    </span>
                  </div>
                )}

                {/* Actions */}
                {!anomaly.dismissed_at && (
                  <div className="mt-3 flex justify-end">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDismiss(anomaly.id)}
                      className="text-xs"
                    >
                      <Eye className="h-3 w-3 mr-1" />
                      Mark as Reviewed
                    </Button>
                  </div>
                )}

                {/* Dismissed Badge */}
                {anomaly.dismissed_at && (
                  <div className="mt-2">
                    <Badge variant="secondary" className="text-xs">
                      Dismissed by {anomaly.dismissed_by || 'system'}
                    </Badge>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
