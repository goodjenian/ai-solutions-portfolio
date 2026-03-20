'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Wind, Volume2, Bus, CheckCircle, AlertTriangle, Info } from 'lucide-react';
import type { NeighborhoodQualityResult } from '@/lib/types';

interface NewFactorsSectionProps {
  result: NeighborhoodQualityResult;
  className?: string;
}

interface NewFactorConfig {
  key: 'air_quality_score' | 'noise_level_score' | 'public_transport_score';
  label: string;
  icon: React.ReactNode;
  detailKey: 'air_quality' | 'noise_level' | 'public_transport';
  description: string;
  getRating: (value: number) => { label: string; color: string; bg: string };
  formatValue: (detail: { raw_value: number; unit: string } | undefined) => string;
}

/**
 * NewFactorsSection Component
 *
 * Displays detailed cards for the three new scoring factors:
 * - Air Quality (AQI-based)
 * - Noise Level (decibel-based)
 * - Public Transport (stop count-based)
 *
 * Each card shows:
 * - Score gauge/chart
 * - Raw value with unit
 * - Data source and confidence indicator
 * - Interpretation of what the score means
 */
export function NewFactorsSection({ result, className = '' }: NewFactorsSectionProps) {
  const getAirQualityRating = (aqi: number) => {
    if (aqi <= 50) {
      return { label: 'Good', color: 'text-green-600', bg: 'bg-green-50 border-green-200' };
    }
    if (aqi <= 100) {
      return { label: 'Moderate', color: 'text-yellow-600', bg: 'bg-yellow-50 border-yellow-200' };
    }
    if (aqi <= 150) {
      return {
        label: 'Unhealthy for Sensitive',
        color: 'text-orange-600',
        bg: 'bg-orange-50 border-orange-200',
      };
    }
    if (aqi <= 200) {
      return { label: 'Unhealthy', color: 'text-red-600', bg: 'bg-red-50 border-red-200' };
    }
    return {
      label: 'Very Unhealthy',
      color: 'text-purple-600',
      bg: 'bg-purple-50 border-purple-200',
    };
  };

  const getNoiseRating = (dB: number) => {
    if (dB <= 45) {
      return { label: 'Quiet', color: 'text-green-600', bg: 'bg-green-50 border-green-200' };
    }
    if (dB <= 55) {
      return { label: 'Moderate', color: 'text-yellow-600', bg: 'bg-yellow-50 border-yellow-200' };
    }
    if (dB <= 65) {
      return { label: 'Noisy', color: 'text-orange-600', bg: 'bg-orange-50 border-orange-200' };
    }
    return { label: 'Very Noisy', color: 'text-red-600', bg: 'bg-red-50 border-red-200' };
  };

  const getTransportRating = (stopCount: number) => {
    if (stopCount >= 10) {
      return { label: 'Excellent', color: 'text-green-600', bg: 'bg-green-50 border-green-200' };
    }
    if (stopCount >= 5) {
      return { label: 'Good', color: 'text-lime-600', bg: 'bg-lime-50 border-lime-200' };
    }
    if (stopCount >= 3) {
      return { label: 'Fair', color: 'text-yellow-600', bg: 'bg-yellow-50 border-yellow-200' };
    }
    return { label: 'Limited', color: 'text-red-600', bg: 'bg-red-50 border-red-200' };
  };

  const formatAirQuality = (detail: { raw_value: number; unit: string } | undefined) => {
    if (!detail) return 'N/A';
    return `AQI ${detail.raw_value}`;
  };

  const formatNoise = (detail: { raw_value: number; unit: string } | undefined) => {
    if (!detail) return 'N/A';
    return `${detail.raw_value} dB`;
  };

  const formatTransport = (detail: { raw_value: number; unit: string } | undefined) => {
    if (!detail) return 'N/A';
    return `${detail.raw_value} stops within 1km`;
  };

  const factorConfigs: NewFactorConfig[] = [
    {
      key: 'air_quality_score',
      label: 'Air Quality',
      icon: <Wind className="h-5 w-5" />,
      detailKey: 'air_quality',
      description:
        'Measures air pollution levels using the Air Quality Index (AQI). Lower values indicate cleaner air.',
      getRating: (_value) => {
        const detail = result.factor_details?.air_quality;
        return detail
          ? getAirQualityRating(detail.raw_value)
          : { label: 'Unknown', color: 'text-gray-600', bg: 'bg-gray-50 border-gray-200' };
      },
      formatValue: formatAirQuality,
    },
    {
      key: 'noise_level_score',
      label: 'Noise Level',
      icon: <Volume2 className="h-5 w-5" />,
      detailKey: 'noise_level',
      description:
        'Average ambient noise level in decibels. Lower values indicate a quieter environment.',
      getRating: (_value) => {
        const detail = result.factor_details?.noise_level;
        return detail
          ? getNoiseRating(detail.raw_value)
          : { label: 'Unknown', color: 'text-gray-600', bg: 'bg-gray-50 border-gray-200' };
      },
      formatValue: formatNoise,
    },
    {
      key: 'public_transport_score',
      label: 'Public Transport',
      icon: <Bus className="h-5 w-5" />,
      detailKey: 'public_transport',
      description:
        'Number of public transport stops within 1km. Higher values indicate better accessibility.',
      getRating: (_value) => {
        const detail = result.factor_details?.public_transport;
        return detail
          ? getTransportRating(detail.raw_value)
          : { label: 'Unknown', color: 'text-gray-600', bg: 'bg-gray-50 border-gray-200' };
      },
      formatValue: formatTransport,
    },
  ];

  const getConfidenceIcon = (confidence: number | undefined) => {
    if (confidence === undefined) {
      return <Info className="h-3 w-3 text-gray-400" />;
    }
    if (confidence >= 0.8) {
      return <CheckCircle className="h-3 w-3 text-green-600" />;
    }
    if (confidence >= 0.6) {
      return <Info className="h-3 w-3 text-yellow-600" />;
    }
    return <AlertTriangle className="h-3 w-3 text-red-600" />;
  };

  const getScoreColor = (score: number): string => {
    if (score >= 85) return 'text-green-600';
    if (score >= 70) return 'text-lime-600';
    if (score >= 55) return 'text-yellow-600';
    if (score >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  return (
    <div className={className}>
      <Card>
        <CardHeader>
          <CardTitle>Extended Quality Factors</CardTitle>
          <CardDescription>
            Additional environmental and accessibility metrics for a complete neighborhood
            assessment
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {factorConfigs.map((config) => {
              const score = result[config.key];
              const detail = result.factor_details?.[config.detailKey];
              const rating = config.getRating(score);
              const confidence = detail?.confidence;

              return (
                <div
                  key={config.key}
                  className={`rounded-lg border-2 p-5 ${rating.bg} transition-all hover:shadow-md`}
                >
                  {/* Header */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <div className={`p-2 rounded-lg bg-white ${rating.color} shadow-sm`}>
                        {config.icon}
                      </div>
                      <div>
                        <h4 className="font-semibold text-sm">{config.label}</h4>
                        <span className={`text-xs font-medium ${rating.color}`}>
                          {rating.label}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Score Gauge */}
                  <div className="flex items-center justify-center mb-4">
                    <div className="relative w-24 h-24">
                      {/* Background circle */}
                      <svg className="w-full h-full transform -rotate-90">
                        <circle
                          cx="48"
                          cy="48"
                          r="40"
                          stroke="currentColor"
                          strokeWidth="8"
                          fill="none"
                          className="text-gray-200"
                        />
                        {/* Score arc */}
                        <circle
                          cx="48"
                          cy="48"
                          r="40"
                          stroke="currentColor"
                          strokeWidth="8"
                          fill="none"
                          strokeDasharray={`${(score / 100) * 251.2} 251.2`}
                          className={getScoreColor(score)}
                          strokeLinecap="round"
                        />
                      </svg>
                      {/* Center score */}
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className={`text-2xl font-bold ${getScoreColor(score)}`}>
                          {score.toFixed(0)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Raw value */}
                  <div className="text-center mb-3">
                    <p className="text-lg font-semibold text-gray-800">
                      {config.formatValue(detail)}
                    </p>
                  </div>

                  {/* Data source info */}
                  {detail && (
                    <div className="flex items-center justify-between text-xs text-muted-foreground mb-3 pb-3 border-b border-gray-200">
                      <span>Source: {detail.data_source}</span>
                      <div
                        className="flex items-center gap-1"
                        title={`Confidence: ${((confidence ?? 0) * 100).toFixed(0)}%`}
                      >
                        {getConfidenceIcon(confidence)}
                        <span
                          className={
                            (confidence ?? 0) >= 0.8
                              ? 'text-green-600'
                              : (confidence ?? 0) >= 0.6
                                ? 'text-yellow-600'
                                : 'text-red-600'
                          }
                        >
                          {((confidence ?? 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Description */}
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {config.description}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Data freshness note */}
          {result.data_freshness && (
            <div className="mt-4 pt-4 border-t">
              <p className="text-xs text-muted-foreground">
                <Info className="h-3 w-3 inline mr-1" />
                Data freshness: Air Quality updated{' '}
                {result.data_freshness.air_quality
                  ? new Date(result.data_freshness.air_quality).toLocaleDateString()
                  : 'N/A'}
                , Noise Level updated{' '}
                {result.data_freshness.noise_level
                  ? new Date(result.data_freshness.noise_level).toLocaleDateString()
                  : 'N/A'}
                , Transport updated{' '}
                {result.data_freshness.public_transport
                  ? new Date(result.data_freshness.public_transport).toLocaleDateString()
                  : 'N/A'}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
