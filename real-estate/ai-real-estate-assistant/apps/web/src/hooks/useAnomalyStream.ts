'use client';

import { useState, useEffect, useCallback } from 'react';
import type { MarketAnomaly } from '@/lib/types';
import { subscribeToAnomalies } from '@/lib/api';

interface UseAnomalyStreamResult {
  anomalies: MarketAnomaly[];
  connected: boolean;
  error: string | null;
  clearAnomalies: () => void;
  removeAnomaly: (anomalyId: string) => void;
}

/**
 * Hook to subscribe to real-time anomaly notifications via Server-Sent Events.
 *
 * @param enabled - Whether to enable the subscription (default: true)
 * @param maxAnomalies - Maximum number of anomalies to keep in state (default: 50)
 *
 * @example
 * ```tsx
 * function AnomalyDashboard() {
 *   const { anomalies, connected, error } = useAnomalyStream();
 *
 *   if (error) return <div>Error: {error}</div>;
 *
 *   return (
 *     <div>
 *       <div>Status: {connected ? 'Connected' : 'Disconnected'}</div>
 *       {anomalies.map(a => <AnomalyCard key={a.id} anomaly={a} />)}
 *     </div>
 *   );
 * }
 * ```
 */
export function useAnomalyStream(
  enabled: boolean = true,
  maxAnomalies: number = 50
): UseAnomalyStreamResult {
  const [anomalies, setAnomalies] = useState<MarketAnomaly[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleNewAnomaly = useCallback(
    (anomaly: MarketAnomaly) => {
      setAnomalies((prev) => {
        // Add new anomaly at the beginning and limit the list size
        const updated = [anomaly, ...prev];
        return updated.slice(0, maxAnomalies);
      });
    },
    [maxAnomalies]
  );

  useEffect(() => {
    let eventSource: EventSource | null = null;
    let reconnectTimeout: NodeJS.Timeout | null = null;

    // Don't connect if disabled
    if (!enabled) {
      return () => {
        // Cleanup: ensure connection is closed
        if (eventSource) {
          eventSource.close();
        }
        if (reconnectTimeout) {
          clearTimeout(reconnectTimeout);
        }
      };
    }

    const connect = () => {
      try {
        eventSource = subscribeToAnomalies();

        eventSource.onopen = () => {
          setConnected(true);
          setError(null);
          console.log('[SSE] Connected to anomaly stream');
        };

        eventSource.onmessage = (event: MessageEvent) => {
          try {
            const anomaly: MarketAnomaly = JSON.parse(event.data);
            handleNewAnomaly(anomaly);
          } catch (err) {
            console.error('[SSE] Failed to parse anomaly:', err);
          }
        };

        eventSource.onerror = (err: Event) => {
          console.error('[SSE] Connection error:', err);
          setConnected(false);
          setError('Connection lost. Reconnecting...');

          // Attempt to reconnect after 5 seconds
          reconnectTimeout = setTimeout(() => {
            connect();
          }, 5000);
        };
      } catch (err) {
        console.error('[SSE] Failed to create EventSource:', err);
        setError('Failed to connect to anomaly stream');
        setConnected(false);
      }
    };

    connect();

    return () => {
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
        reconnectTimeout = null;
      }
      setConnected(false);
    };
  }, [enabled, handleNewAnomaly]);

  /**
   * Clear all anomalies
   */
  const clearAnomalies = useCallback(() => {
    setAnomalies([]);
  }, []);

  /**
   * Remove a specific anomaly
   */
  const removeAnomaly = useCallback((anomalyId: string) => {
    setAnomalies((prev) => prev.filter((a) => a.id !== anomalyId));
  }, []);

  return {
    anomalies,
    connected,
    error,
    clearAnomalies,
    removeAnomaly,
  };
}

export default useAnomalyStream;
