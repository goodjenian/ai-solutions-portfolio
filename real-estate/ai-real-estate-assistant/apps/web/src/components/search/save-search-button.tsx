'use client';

import React, { useState } from 'react';
import { Bookmark, Loader2, X } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { createSavedSearch, ApiError } from '@/lib/api';
import type { AlertFrequency } from '@/lib/types';

interface SaveSearchButtonProps {
  filters: Record<string, unknown>;
  query?: string;
  onSaveSuccess?: () => void;
  className?: string;
}

export function SaveSearchButton({
  filters,
  query,
  onSaveSuccess,
  className,
}: SaveSearchButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState('');
  const [alertFrequency, setAlertFrequency] = useState<AlertFrequency>('daily');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleOpen = () => {
    setIsOpen(true);
    setError(null);
    setSuccess(false);
    // Pre-fill name from query if available
    if (query && !name) {
      setName(query.slice(0, 100));
    }
  };

  const handleClose = () => {
    setIsOpen(false);
    setName('');
    setError(null);
    setSuccess(false);
  };

  const handleSave = async () => {
    if (!name.trim()) {
      setError('Please enter a name for this search');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      await createSavedSearch({
        name: name.trim(),
        filters,
        alert_frequency: alertFrequency,
        notify_on_new: true,
        notify_on_price_drop: true,
      });
      setSuccess(true);
      setTimeout(() => {
        handleClose();
        onSaveSuccess?.();
      }, 1500);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.category === 'auth') {
          setError('Please log in to save searches');
        } else {
          setError(err.message);
        }
      } else {
        setError(err instanceof Error ? err.message : 'Failed to save search');
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <Button variant="outline" onClick={handleOpen} className={className}>
        <Bookmark className="h-4 w-4 mr-2" />
        Save Search
      </Button>

      {isOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-background rounded-lg p-6 max-w-md w-full mx-4 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Save Search</h2>
              <button onClick={handleClose} className="text-muted-foreground hover:text-foreground">
                <X className="h-5 w-5" />
              </button>
            </div>

            {success ? (
              <div className="text-center py-4">
                <div className="text-green-600 mb-2">Search saved successfully!</div>
                <p className="text-sm text-muted-foreground">
                  You will receive alerts based on your preferences.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Search Name</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g., 2-bed apartments in Madrid"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                    maxLength={255}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Alert Frequency</label>
                  <select
                    value={alertFrequency}
                    onChange={(e) => setAlertFrequency(e.target.value as AlertFrequency)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  >
                    <option value="instant">Instant - Get notified immediately</option>
                    <option value="daily">Daily Digest - Summary once per day</option>
                    <option value="weekly">Weekly Digest - Summary once per week</option>
                    <option value="none">No Alerts - Just save for later</option>
                  </select>
                </div>

                <div className="text-sm text-muted-foreground">
                  You&apos;ll be notified about new properties and price drops matching this search.
                </div>

                {error && <p className="text-sm text-destructive">{error}</p>}

                <div className="flex justify-end gap-2 pt-2">
                  <Button variant="outline" onClick={handleClose} disabled={saving}>
                    Cancel
                  </Button>
                  <Button onClick={handleSave} disabled={saving}>
                    {saving ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      'Save'
                    )}
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
