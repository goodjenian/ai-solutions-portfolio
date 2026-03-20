'use client';

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { NeighborhoodQualityResult } from '@/lib/types';

interface CityComparisonCardProps {
  result: NeighborhoodQualityResult;
  className?: string;
}

/**
 * CityComparisonCard Component
 *
 * Displays how the neighborhood compares to the city average including:
 * - Percentile rank (0-100)
 * - Better/worse than average factors
 * - Visual comparison chart
 */
export function CityComparisonCard({ result, className = '' }: CityComparisonCardProps) {
  const comparison = result.city_comparison;

  if (!comparison) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>City Comparison</CardTitle>
          <CardDescription>How this neighborhood compares to the city average</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8 text-muted-foreground">
            <p className="text-sm">City comparison data not available for this location.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const getPercentileColor = (percentile: number): string => {
    if (percentile >= 80) return 'text-green-600';
    if (percentile >= 60) return 'text-lime-600';
    if (percentile >= 40) return 'text-yellow-600';
    if (percentile >= 20) return 'text-orange-600';
    return 'text-red-600';
  };

  const getPercentileLabel = (percentile: number): string => {
    if (percentile >= 90) return 'Outstanding';
    if (percentile >= 75) return 'Excellent';
    if (percentile >= 60) return 'Above Average';
    if (percentile >= 40) return 'Average';
    if (percentile >= 25) return 'Below Average';
    return 'Poor';
  };

  // Prepare chart data
  const chartData = [
    {
      name: 'This Area',
      score: result.overall_score,
      fill: '#3b82f6',
    },
    {
      name: 'City Avg',
      score: comparison.city_average,
      fill: '#94a3b8',
    },
  ];

  // Factor labels mapping
  const factorLabels: Record<string, string> = {
    safety_score: 'Safety',
    schools_score: 'Schools',
    amenities_score: 'Amenities',
    walkability_score: 'Walkability',
    green_space_score: 'Green Space',
    air_quality_score: 'Air Quality',
    noise_level_score: 'Noise Level',
    public_transport_score: 'Public Transport',
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>City Comparison</CardTitle>
        <CardDescription>
          How this neighborhood compares to {result.city || 'the city'} average
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Percentile Rank */}
        <div className="flex flex-col sm:flex-row items-center gap-6 mb-6">
          {/* Circular percentile indicator */}
          <div className="flex-shrink-0">
            <div className="relative w-32 h-32">
              <svg className="w-full h-full transform -rotate-90">
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke="currentColor"
                  strokeWidth="12"
                  fill="none"
                  className="text-gray-200"
                />
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke="currentColor"
                  strokeWidth="12"
                  fill="none"
                  strokeDasharray={`${(comparison.percentile / 100) * 351.86} 351.86`}
                  className={getPercentileColor(comparison.percentile)}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={`text-3xl font-bold ${getPercentileColor(comparison.percentile)}`}>
                  {comparison.percentile}
                </span>
                <span className="text-xs text-muted-foreground">percentile</span>
              </div>
            </div>
          </div>

          {/* Percentile info */}
          <div className="flex-1 text-center sm:text-left">
            <h4 className="text-lg font-semibold mb-1">
              {getPercentileLabel(comparison.percentile)}
            </h4>
            <p className="text-sm text-muted-foreground mb-2">
              This neighborhood scores higher than{' '}
              <span className="font-semibold">{comparison.percentile}%</span> of areas in{' '}
              {result.city || 'the city'}
            </p>
            <div className="flex items-center gap-2 justify-center sm:justify-start">
              <span className="text-sm text-muted-foreground">City Average:</span>
              <span className="text-lg font-bold text-gray-600">
                {comparison.city_average.toFixed(1)}
              </span>
            </div>
          </div>
        </div>

        {/* Comparison Chart */}
        <div className="mb-6">
          <h5 className="text-sm font-medium mb-3">Score Comparison</h5>
          <div className="h-40">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical" barSize={40}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fontSize: 12 }}
                  width={80}
                  tickLine={false}
                />
                <Tooltip
                  formatter={(value: number) => [value.toFixed(1), 'Score']}
                  contentStyle={{ fontSize: '12px' }}
                />
                <Bar dataKey="score" radius={[4, 4, 4, 4]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Better/Worse factors */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Better than average */}
          {comparison.better_than.length > 0 && (
            <div className="rounded-lg border border-green-200 bg-green-50 p-4">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="h-4 w-4 text-green-600" />
                <h5 className="text-sm font-semibold text-green-800">Better Than Average</h5>
              </div>
              <ul className="space-y-1">
                {comparison.better_than.map((factor) => {
                  const factorKey = `${factor.toLowerCase().replace(' ', '_')}_score`;
                  const score = result[factorKey as keyof NeighborhoodQualityResult] as number;
                  return (
                    <li key={factor} className="flex items-center justify-between text-xs">
                      <span className="text-green-700">{factorLabels[factorKey] || factor}</span>
                      <span className="font-semibold text-green-800">{score?.toFixed(1)}</span>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}

          {/* Worse than average */}
          {comparison.worse_than.length > 0 && (
            <div className="rounded-lg border border-orange-200 bg-orange-50 p-4">
              <div className="flex items-center gap-2 mb-3">
                <TrendingDown className="h-4 w-4 text-orange-600" />
                <h5 className="text-sm font-semibold text-orange-800">Below Average</h5>
              </div>
              <ul className="space-y-1">
                {comparison.worse_than.map((factor) => {
                  const factorKey = `${factor.toLowerCase().replace(' ', '_')}_score`;
                  const score = result[factorKey as keyof NeighborhoodQualityResult] as number;
                  return (
                    <li key={factor} className="flex items-center justify-between text-xs">
                      <span className="text-orange-700">{factorLabels[factorKey] || factor}</span>
                      <span className="font-semibold text-orange-800">{score?.toFixed(1)}</span>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}

          {/* All equal case */}
          {comparison.better_than.length === 0 && comparison.worse_than.length === 0 && (
            <div className="md:col-span-2 rounded-lg border border-gray-200 bg-gray-50 p-4">
              <div className="flex items-center gap-2">
                <Minus className="h-4 w-4 text-gray-600" />
                <p className="text-sm text-gray-600">
                  This neighborhood scores close to the city average across all factors.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Overall diff badge */}
        <div className="mt-4 pt-4 border-t flex items-center justify-center">
          <div
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${
              result.overall_score > comparison.city_average
                ? 'bg-green-100 text-green-800'
                : result.overall_score < comparison.city_average
                  ? 'bg-orange-100 text-orange-800'
                  : 'bg-gray-100 text-gray-800'
            }`}
          >
            {result.overall_score > comparison.city_average ? (
              <TrendingUp className="h-4 w-4" />
            ) : result.overall_score < comparison.city_average ? (
              <TrendingDown className="h-4 w-4" />
            ) : (
              <Minus className="h-4 w-4" />
            )}
            <span className="text-sm font-medium">
              {result.overall_score > comparison.city_average
                ? `${(result.overall_score - comparison.city_average).toFixed(1)} points above average`
                : result.overall_score < comparison.city_average
                  ? `${(comparison.city_average - result.overall_score).toFixed(1)} points below average`
                  : 'Equal to city average'}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
