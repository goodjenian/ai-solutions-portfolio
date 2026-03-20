'use client';

import React, { useEffect, useState } from 'react';
import {
  Bookmark,
  Bell,
  BellOff,
  Trash2,
  Search,
  Loader2,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { getSavedSearches, deleteSavedSearch, toggleSavedSearchAlert, ApiError } from '@/lib/api';
import type { SavedSearch } from '@/lib/types';

export default function SavedSearchesPage() {
  const [searches, setSearches] = useState<SavedSearch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    fetchSearches();
  }, []);

  const fetchSearches = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getSavedSearches(true);
      setSearches(data.items);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.category === 'auth') {
          setError('Please log in to view your saved searches');
        } else {
          setError(err.message);
        }
      } else {
        setError(err instanceof Error ? err.message : 'Failed to load saved searches');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleToggleAlert = async (id: string, currentState: boolean) => {
    try {
      setActionLoading(id);
      const updated = await toggleSavedSearchAlert(id, !currentState);
      setSearches(searches.map((s) => (s.id === id ? updated : s)));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle alert');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete "${name}"?`)) {
      return;
    }

    try {
      setActionLoading(id);
      await deleteSavedSearch(id);
      setSearches(searches.filter((s) => s.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete search');
    } finally {
      setActionLoading(null);
    }
  };

  const formatFilters = (filters: Record<string, unknown>): string => {
    const parts: string[] = [];
    if (filters.city) parts.push(filters.city as string);
    if (filters.min_price || filters.max_price) {
      const min = filters.min_price ? `$${Number(filters.min_price).toLocaleString()}` : '';
      const max = filters.max_price ? `$${Number(filters.max_price).toLocaleString()}` : '';
      if (min && max) {
        parts.push(`${min}-${max}`);
      } else {
        parts.push(`${min}${max}`);
      }
    }
    if (filters.property_types && Array.isArray(filters.property_types)) {
      parts.push(filters.property_types.join(', '));
    }
    if (filters.min_rooms || filters.max_rooms) {
      const min = filters.min_rooms || '';
      const max = filters.max_rooms || '';
      parts.push(`${min}-${max} rooms`);
    }
    return parts.join(' | ') || 'All properties';
  };

  const formatFrequency = (frequency: string): string => {
    switch (frequency) {
      case 'instant':
        return 'Instant';
      case 'daily':
        return 'Daily';
      case 'weekly':
        return 'Weekly';
      case 'none':
        return 'None';
      default:
        return frequency;
    }
  };

  const formatDate = (dateStr: string): string => {
    try {
      return new Date(dateStr).toLocaleDateString();
    } catch {
      return dateStr;
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <Bookmark className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-3xl font-bold">Saved Searches</h1>
            <p className="text-muted-foreground">
              Manage your saved searches and alert preferences
            </p>
          </div>
        </div>
        <Button variant="outline" onClick={fetchSearches} disabled={loading}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {error && (
        <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-md mb-6 flex items-center gap-2">
          <AlertCircle className="h-5 w-5" />
          {error}
        </div>
      )}

      {searches.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Search className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold">No saved searches yet</h3>
            <p className="text-muted-foreground mt-2 text-center max-w-md">
              Save searches from the search page to get notified about new properties that match
              your criteria.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {searches.map((search) => (
            <Card key={search.id}>
              <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                <div className="flex-1">
                  <CardTitle className="text-lg flex items-center gap-2">
                    {search.name}
                    {!search.is_active && (
                      <span className="text-xs font-normal text-muted-foreground bg-muted px-2 py-0.5 rounded">
                        Paused
                      </span>
                    )}
                  </CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">
                    {formatFilters(search.filters)}
                  </p>
                </div>
                <div className="flex items-center gap-2 ml-4">
                  <Button
                    variant={search.is_active ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleToggleAlert(search.id, search.is_active)}
                    disabled={actionLoading === search.id}
                    title={search.is_active ? 'Pause alerts' : 'Resume alerts'}
                  >
                    {actionLoading === search.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : search.is_active ? (
                      <Bell className="h-4 w-4" />
                    ) : (
                      <BellOff className="h-4 w-4" />
                    )}
                    <span className="ml-2 hidden sm:inline">
                      {formatFrequency(search.alert_frequency)}
                    </span>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDelete(search.id, search.name)}
                    disabled={actionLoading === search.id}
                    title="Delete search"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
                  <span>Created: {formatDate(search.created_at)}</span>
                  <span>Used: {search.use_count} times</span>
                  {search.notify_on_new && <span className="text-green-600">New matches</span>}
                  {search.notify_on_price_drop && (
                    <span className="text-blue-600">Price drops</span>
                  )}
                </div>
                {search.description && (
                  <p className="text-sm text-muted-foreground mt-2">{search.description}</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
