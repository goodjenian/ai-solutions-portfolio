'use client';

import React from 'react';
import type { NeighborhoodQualityResult } from '@/lib/types';
import {
  Shield,
  GraduationCap,
  ShoppingBag,
  Footprints,
  Trees,
  Wind,
  Volume2,
  Bus,
} from 'lucide-react';

interface FactorBreakdownProps {
  result: NeighborhoodQualityResult;
  compact?: boolean;
  className?: string;
}

interface FactorConfig {
  key: keyof NeighborhoodQualityResult;
  label: string;
  icon: React.ReactNode;
  weight: string;
  description: string;
  color: string;
  bgColor: string;
}

/**
 * FactorBreakdown Component
 *
 * Displays a grid of all 8 neighborhood quality factors with their scores,
 * weights, and confidence indicators.
 *
 * Shows:
 * - Core factors (60%): Safety, Schools, Amenities, Walkability, Green Space
 * - New factors (40%): Air Quality, Noise Level, Public Transport
 */
export function FactorBreakdown({ result, compact = false, className = '' }: FactorBreakdownProps) {
  const factorConfigs: FactorConfig[] = [
    {
      key: 'safety_score',
      label: 'Safety',
      icon: <Shield className="h-4 w-4" />,
      weight: '15%',
      description: 'Crime rate and police proximity',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      key: 'schools_score',
      label: 'Schools',
      icon: <GraduationCap className="h-4 w-4" />,
      weight: '15%',
      description: 'School quality and proximity',
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
    },
    {
      key: 'amenities_score',
      label: 'Amenities',
      icon: <ShoppingBag className="h-4 w-4" />,
      weight: '15%',
      description: 'Shops, restaurants, services',
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
    {
      key: 'walkability_score',
      label: 'Walkability',
      icon: <Footprints className="h-4 w-4" />,
      weight: '15%',
      description: 'Pedestrian-friendly infrastructure',
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      key: 'green_space_score',
      label: 'Green Space',
      icon: <Trees className="h-4 w-4" />,
      weight: '10%',
      description: 'Parks and natural areas',
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
    },
    {
      key: 'air_quality_score',
      label: 'Air Quality',
      icon: <Wind className="h-4 w-4" />,
      weight: '10%',
      description: 'Air pollution index (AQI)',
      color: 'text-cyan-600',
      bgColor: 'bg-cyan-50',
    },
    {
      key: 'noise_level_score',
      label: 'Noise Level',
      icon: <Volume2 className="h-4 w-4" />,
      weight: '10%',
      description: 'Ambient noise levels',
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
    {
      key: 'public_transport_score',
      label: 'Public Transport',
      icon: <Bus className="h-4 w-4" />,
      weight: '10%',
      description: 'Transit accessibility',
      color: 'text-rose-600',
      bgColor: 'bg-rose-50',
    },
  ];

  const getScoreColor = (score: number): string => {
    if (score >= 85) return 'bg-green-500';
    if (score >= 70) return 'bg-lime-500';
    if (score >= 55) return 'bg-yellow-500';
    if (score >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getConfidenceIndicator = (factorKey: string): { level: string; color: string } => {
    const detail = result.factor_details?.[factorKey as keyof typeof result.factor_details];
    if (!detail) {
      return { level: 'N/A', color: 'text-gray-400' };
    }

    if (detail.confidence >= 0.8) {
      return { level: 'High', color: 'text-green-600' };
    }
    if (detail.confidence >= 0.6) {
      return { level: 'Medium', color: 'text-yellow-600' };
    }
    return { level: 'Low', color: 'text-red-600' };
  };

  if (compact) {
    // Compact version: smaller cards in a grid
    return (
      <div className={`grid grid-cols-2 md:grid-cols-4 gap-3 ${className}`}>
        {factorConfigs.map((config) => {
          const score = result[config.key] as number;

          return (
            <div
              key={config.key}
              className={`rounded-lg border p-3 ${config.bgColor} border-${config.color.split('-')[1]}-200`}
            >
              <div className="flex items-center gap-2 mb-2">
                <div className={`${config.color}`}>{config.icon}</div>
                <span className="text-sm font-medium">{config.label}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className={`text-xl font-bold ${config.color}`}>{score.toFixed(1)}</span>
                <span className="text-xs text-muted-foreground">{config.weight}</span>
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  // Full version: detailed cards with more information
  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Quality Factors Breakdown</h3>
        <div className="text-sm text-muted-foreground">
          Overall: <span className="font-semibold">{result.overall_score.toFixed(1)}/100</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {factorConfigs.map((config) => {
          const score = result[config.key] as number;
          const confidence = getConfidenceIndicator(config.key);
          const detail = result.factor_details?.[config.key as keyof typeof result.factor_details];

          return (
            <div
              key={config.key}
              className="rounded-lg border bg-card p-4 shadow-sm hover:shadow-md transition-shadow"
            >
              {/* Header with icon and label */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className={`p-2 rounded-lg ${config.bgColor} ${config.color}`}>
                    {config.icon}
                  </div>
                  <div>
                    <p className="font-semibold text-sm">{config.label}</p>
                    <p className="text-xs text-muted-foreground">{config.weight}</p>
                  </div>
                </div>
              </div>

              {/* Score display */}
              <div className="mb-3">
                <div className="flex items-end justify-between mb-2">
                  <span className={`text-3xl font-bold ${config.color}`}>{score.toFixed(1)}</span>
                  <span className="text-xs text-muted-foreground">/ 100</span>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${getScoreColor(score)}`}
                    style={{ width: `${Math.min(score, 100)}%` }}
                    role="progressbar"
                    aria-valuenow={score}
                    aria-valuemin={0}
                    aria-valuemax={100}
                  />
                </div>
              </div>

              {/* Description */}
              <p className="text-xs text-muted-foreground mb-2">{config.description}</p>

              {/* Confidence indicator */}
              {detail && (
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Data confidence:</span>
                  <span className={confidence.color}>{confidence.level}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground pt-2 border-t">
        <span className="font-medium">Score ranges:</span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-green-500" />
          85+ Excellent
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-lime-500" />
          70-84 Good
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-yellow-500" />
          55-69 Fair
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-orange-500" />
          40-54 Poor
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-red-500" />
          &lt;40 Very Poor
        </span>
      </div>
    </div>
  );
}
