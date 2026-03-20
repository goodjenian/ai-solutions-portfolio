"use client";

import React from "react";

interface NeighborhoodBadgeProps {
  overallScore: number;
  showLabel?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

/**
 * Neighborhood Quality Badge Component
 *
 * Displays a color-coded badge showing neighborhood quality score.
 * Used on property cards, search results, and detail pages.
 *
 * Color coding:
 * - 85+ (Excellent): Green
 * - 70-84 (Good): Lime
 * - 55-69 (Fair): Yellow
 * - 40-54 (Poor): Orange
 * - <40 (Very Poor): Red
 */
export function NeighborhoodBadge({
  overallScore,
  showLabel = true,
  size = "md",
  className = "",
}: NeighborhoodBadgeProps) {
  const getScoreColor = (): string => {
    if (overallScore >= 85) return "text-green-600";
    if (overallScore >= 70) return "text-lime-600";
    if (overallScore >= 55) return "text-yellow-600";
    if (overallScore >= 40) return "text-orange-600";
    return "text-red-600";
  };

  const getBgColor = (): string => {
    if (overallScore >= 85) return "bg-green-50";
    if (overallScore >= 70) return "bg-lime-50";
    if (overallScore >= 55) return "bg-yellow-50";
    if (overallScore >= 40) return "bg-orange-50";
    return "bg-red-50";
  };

  const getBorderColor = (): string => {
    if (overallScore >= 85) return "border-green-200";
    if (overallScore >= 70) return "border-lime-200";
    if (overallScore >= 55) return "border-yellow-200";
    if (overallScore >= 40) return "border-orange-200";
    return "border-red-200";
  };

  const getRatingLabel = (): string => {
    if (overallScore >= 85) return "Excellent";
    if (overallScore >= 70) return "Good";
    if (overallScore >= 55) return "Fair";
    if (overallScore >= 40) return "Poor";
    return "Very Poor";
  };

  const getRatingLabelShort = (): string => {
    if (overallScore >= 85) return "Exc";
    if (overallScore >= 70) return "Good";
    if (overallScore >= 55) return "Fair";
    if (overallScore >= 40) return "Poor";
    return "VPoor";
  };

  const sizeClasses = {
    sm: {
      container: "px-2 py-0.5 text-xs",
      score: "text-sm font-semibold",
      label: "text-xs",
    },
    md: {
      container: "px-2.5 py-1 text-xs",
      score: "text-base font-semibold",
      label: "text-xs",
    },
    lg: {
      container: "px-3 py-1.5 text-sm",
      score: "text-lg font-bold",
      label: "text-sm",
    },
  };

  const classes = sizeClasses[size];
  const scoreColor = getScoreColor();
  const bgColor = getBgColor();
  const borderColor = getBorderColor();

  return (
    <div
      className={`inline-flex items-center gap-1.5 rounded-full border ${bgColor} ${borderColor} ${classes.container} ${className}`}
      title={`Neighborhood Quality: ${getRatingLabel()} (${overallScore}/100)`}
    >
      {/* Score */}
      <span className={`${scoreColor} ${classes.score}`}>
        {overallScore.toFixed(1)}
      </span>

      {/* Label */}
      {showLabel && (
        <span className={`${scoreColor} ${classes.label} font-medium`}>
          {getRatingLabelShort()}
        </span>
      )}
    </div>
  );
}

/**
 * Compact Neighborhood Badge
 *
 * Minimal version showing only the score circle with color indicator.
 * Useful for tight spaces like property card headers.
 */
interface NeighborhoodBadgeCircleProps {
  overallScore: number;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function NeighborhoodBadgeCircle({
  overallScore,
  size = "md",
  className = "",
}: NeighborhoodBadgeCircleProps) {
  const getBgColor = (): string => {
    if (overallScore >= 85) return "bg-green-500";
    if (overallScore >= 70) return "bg-lime-500";
    if (overallScore >= 55) return "bg-yellow-500";
    if (overallScore >= 40) return "bg-orange-500";
    return "bg-red-500";
  };

  const sizeClasses = {
    sm: "w-5 h-5 text-[10px]",
    md: "w-6 h-6 text-xs",
    lg: "w-8 h-8 text-sm",
  };

  return (
    <div
      className={`inline-flex items-center justify-center rounded-full ${getBgColor()} text-white ${sizeClasses[size]} ${className}`}
      title={`Neighborhood Quality: ${overallScore.toFixed(1)}/100`}
    >
      {overallScore.toFixed(0)}
    </div>
  );
}

/**
 * Detailed Neighborhood Score Display
 *
 * Full breakdown display with all component scores.
 * Useful for detail pages and expanded views.
 */
interface NeighborhoodScoreDisplayProps {
  result: {
    overall_score: number;
    safety_score: number;
    schools_score: number;
    amenities_score: number;
    walkability_score: number;
    green_space_score: number;
  };
  compact?: boolean;
  className?: string;
}

export function NeighborhoodScoreDisplay({
  result,
  compact = false,
  className = "",
}: NeighborhoodScoreDisplayProps) {
  const getScoreColor = (score: number): string => {
    if (score >= 85) return "bg-green-500";
    if (score >= 70) return "bg-lime-500";
    if (score >= 55) return "bg-yellow-500";
    if (score >= 40) return "bg-orange-500";
    return "bg-red-500";
  };

  const components = [
    { label: "Safety", score: result.safety_score, weight: "25%" },
    { label: "Schools", score: result.schools_score, weight: "20%" },
    { label: "Amenities", score: result.amenities_score, weight: "20%" },
    { label: "Walkability", score: result.walkability_score, weight: "20%" },
    { label: "Green Space", score: result.green_space_score, weight: "15%" },
  ];

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Overall Score */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">Overall Score</span>
        <NeighborhoodBadge
          overallScore={result.overall_score}
          size={compact ? "sm" : "md"}
        />
      </div>

      {/* Component Scores */}
      {!compact && (
        <div className="space-y-2">
          {components.map((component) => (
            <div
              key={component.label}
              className="flex items-center justify-between text-sm"
            >
              <span className="text-gray-600">
                {component.label} <span className="text-gray-400">({component.weight})</span>
              </span>
              <div className="flex items-center gap-2">
                <div className="w-32 bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${getScoreColor(component.score)}`}
                    style={{ width: `${component.score}%` }}
                  />
                </div>
                <span className="text-gray-600 w-12 text-right">
                  {component.score.toFixed(1)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
