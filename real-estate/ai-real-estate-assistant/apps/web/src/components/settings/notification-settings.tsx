'use client';

import React, { useEffect, useState } from 'react';
import { Bell, Smartphone } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Label } from '../ui/label';
import { getNotificationSettings, updateNotificationSettings } from '@/lib/api';
import { NotificationSettings as SettingsType } from '@/lib/types';
import {
  isPushSupported,
  requestNotificationPermission,
  getNotificationPermission,
} from '@/lib/push';

export function NotificationSettings() {
  const [settings, setSettings] = useState<SettingsType | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [pushPermissionStatus, setPushPermissionStatus] = useState<NotificationPermission | null>(
    null
  );

  useEffect(() => {
    fetchSettings();
    checkPushStatus();
  }, []);

  const fetchSettings = async () => {
    try {
      const data = await getNotificationSettings();
      setSettings(data);
      setError(null);
    } catch {
      setError('Failed to load settings. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const checkPushStatus = async () => {
    if (isPushSupported()) {
      const status = await getNotificationPermission();
      setPushPermissionStatus(status);
    }
  };

  if (loading) {
    return <div className="p-4 text-center">Loading settings...</div>;
  }

  if (!settings) {
    return (
      <div className="p-4 text-center text-red-500">
        {error || 'Something went wrong.'}
        <Button onClick={fetchSettings} className="ml-4">
          Retry
        </Button>
      </div>
    );
  }

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const updated = await updateNotificationSettings(settings);
      setSettings(updated);
      setSuccess('Settings saved successfully.');
    } catch {
      setError('Failed to save settings. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const toggleSetting = (key: Exclude<keyof SettingsType, 'frequency'>) => {
    setSettings({ ...settings, [key]: !settings[key] });
  };

  const handleEnablePush = async () => {
    const permission = await requestNotificationPermission();
    setPushPermissionStatus(permission);
    if (permission === 'granted') {
      setSettings({ ...settings, push_enabled: true });
    }
  };

  return (
    <div className="grid gap-6">
      {/* Push Notifications Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Smartphone className="h-5 w-5 text-primary" />
            <CardTitle>Push Notifications</CardTitle>
          </div>
          <CardDescription>
            Get instant alerts on your device for price drops and new properties.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!isPushSupported() && (
            <div className="rounded-md bg-muted p-3 text-sm text-muted-foreground">
              Push notifications are not supported in this browser.
            </div>
          )}

          {pushPermissionStatus === 'denied' && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              Push notifications are blocked. Please enable them in your browser settings.
            </div>
          )}

          {pushPermissionStatus === 'default' && (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Enable push notifications to receive instant alerts about properties.
              </p>
              <Button onClick={handleEnablePush} className="w-full sm:w-auto">
                <Bell className="mr-2 h-4 w-4" />
                Enable Push Notifications
              </Button>
            </div>
          )}

          {pushPermissionStatus === 'granted' && (
            <>
              <div className="flex items-center justify-between space-x-2">
                <Label htmlFor="push_price_alerts" className="flex flex-col space-y-1">
                  <span>Price Drop Alerts</span>
                  <span className="font-normal text-muted-foreground">
                    Get notified when a saved property&apos;s price decreases.
                  </span>
                </Label>
                <input
                  type="checkbox"
                  id="push_price_alerts"
                  className="h-4 w-4 rounded border-gray-300"
                  checked={settings.push_price_alerts}
                  onChange={() => toggleSetting('push_price_alerts')}
                />
              </div>

              <div className="flex items-center justify-between space-x-2">
                <Label htmlFor="push_new_properties" className="flex flex-col space-y-1">
                  <span>New Property Alerts</span>
                  <span className="font-normal text-muted-foreground">
                    Get notified when new properties match your saved searches.
                  </span>
                </Label>
                <input
                  type="checkbox"
                  id="push_new_properties"
                  className="h-4 w-4 rounded border-gray-300"
                  checked={settings.push_new_properties}
                  onChange={() => toggleSetting('push_new_properties')}
                />
              </div>

              <div className="flex items-center justify-between space-x-2">
                <Label htmlFor="push_saved_searches" className="flex flex-col space-y-1">
                  <span>Saved Search Updates</span>
                  <span className="font-normal text-muted-foreground">
                    Get notified about updates to your saved search results.
                  </span>
                </Label>
                <input
                  type="checkbox"
                  id="push_saved_searches"
                  className="h-4 w-4 rounded border-gray-300"
                  checked={settings.push_saved_searches}
                  onChange={() => toggleSetting('push_saved_searches')}
                />
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Email Digests Card */}
      <Card>
        <CardHeader>
          <CardTitle>Email Digests</CardTitle>
          <CardDescription>
            Manage your property digest subscriptions and frequency.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between space-x-2">
            <Label htmlFor="email_digest" className="flex flex-col space-y-1">
              <span>Consumer Digest</span>
              <span className="font-normal text-muted-foreground">
                Receive new matches and price drops for your saved searches.
              </span>
            </Label>
            <input
              type="checkbox"
              id="email_digest"
              className="h-4 w-4 rounded border-gray-300"
              checked={settings.email_digest}
              onChange={() => toggleSetting('email_digest')}
            />
          </div>

          <div className="flex items-center justify-between space-x-2">
            <Label htmlFor="expert_mode" className="flex flex-col space-y-1">
              <span>Expert Mode</span>
              <span className="font-normal text-muted-foreground">
                Include market trends, indices, and yield analysis in your digest.
              </span>
            </Label>
            <input
              type="checkbox"
              id="expert_mode"
              className="h-4 w-4 rounded border-gray-300"
              checked={settings.expert_mode}
              onChange={() => toggleSetting('expert_mode')}
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="frequency">Digest Frequency</Label>
            <select
              id="frequency"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              value={settings.frequency}
              onChange={(e) =>
                setSettings({ ...settings, frequency: e.target.value as 'daily' | 'weekly' })
              }
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
            </select>
          </div>

          <div className="flex items-center justify-between space-x-2">
            <Label htmlFor="marketing_emails" className="flex flex-col space-y-1">
              <span>Product Updates</span>
              <span className="font-normal text-muted-foreground">
                Receive occasional emails about new features and improvements.
              </span>
            </Label>
            <input
              type="checkbox"
              id="marketing_emails"
              className="h-4 w-4 rounded border-gray-300"
              checked={settings.marketing_emails}
              onChange={() => toggleSetting('marketing_emails')}
            />
          </div>
        </CardContent>
      </Card>

      <div className="flex items-center justify-end gap-4">
        {success && <span className="text-green-600 text-sm">{success}</span>}
        {error && <span className="text-red-600 text-sm">{error}</span>}
        <Button onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save Preferences'}
        </Button>
      </div>
    </div>
  );
}
