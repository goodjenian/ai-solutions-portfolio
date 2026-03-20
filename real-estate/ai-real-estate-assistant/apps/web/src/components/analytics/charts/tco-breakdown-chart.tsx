'use client';

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { TooltipProps } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import type { TCOResult } from '@/lib/types';

interface TCOBreakdownChartProps {
  tcoResult: TCOResult;
  className?: string;
  title?: string;
  description?: string;
}

const COLORS = [
  '#3b82f6', // blue - mortgage
  '#22c55e', // green - property tax
  '#f59e0b', // amber - insurance
  '#8b5cf6', // violet - HOA
  '#06b6d4', // cyan - utilities
  '#ec4899', // pink - internet
  '#84cc16', // lime - parking
  '#ef4444', // red - maintenance
];

const CATEGORY_LABELS: Record<string, string> = {
  mortgage: 'Mortgage',
  property_tax: 'Property Tax',
  insurance: 'Insurance',
  hoa: 'HOA',
  utilities: 'Utilities',
  internet: 'Internet',
  parking: 'Parking',
  maintenance: 'Maintenance',
};

function formatCurrency(value: number) {
  return `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

export function TCOBreakdownChart({
  tcoResult,
  className,
  title = 'Monthly Cost Breakdown',
  description = 'Distribution of ownership costs',
}: TCOBreakdownChartProps) {
  // Build chart data from TCO result
  const chartData = [
    { name: CATEGORY_LABELS.mortgage, value: tcoResult.monthly_mortgage, key: 'mortgage' },
    {
      name: CATEGORY_LABELS.property_tax,
      value: tcoResult.monthly_property_tax,
      key: 'property_tax',
    },
    { name: CATEGORY_LABELS.insurance, value: tcoResult.monthly_insurance, key: 'insurance' },
    { name: CATEGORY_LABELS.hoa, value: tcoResult.monthly_hoa, key: 'hoa' },
    { name: CATEGORY_LABELS.utilities, value: tcoResult.monthly_utilities, key: 'utilities' },
    { name: CATEGORY_LABELS.internet, value: tcoResult.monthly_internet, key: 'internet' },
    { name: CATEGORY_LABELS.parking, value: tcoResult.monthly_parking, key: 'parking' },
    { name: CATEGORY_LABELS.maintenance, value: tcoResult.monthly_maintenance, key: 'maintenance' },
  ].filter((item) => item.value > 0); // Only show non-zero categories

  const renderLabel = ({ name, percent }: { name: string; percent: number }) => {
    if (percent < 0.05) return null;
    return `${name} (${(percent * 100).toFixed(0)}%)`;
  };

  const renderTooltip = ({ active, payload }: TooltipProps<number, string>) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      if (!data || data.value === undefined) return null;
      const percent = (data.value / tcoResult.monthly_tco) * 100;
      return (
        <div className="bg-background border rounded-lg p-3 shadow-lg">
          <p className="font-medium">{data.name}</p>
          <p className="text-sm text-muted-foreground">{formatCurrency(data.value)}/month</p>
          <p className="text-xs text-muted-foreground">{percent.toFixed(1)}% of total</p>
        </div>
      );
    }
    return null;
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={true}
                label={renderLabel}
                outerRadius={90}
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${entry.key}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={renderTooltip} />
              <Legend formatter={(value: string) => <span className="text-sm">{value}</span>} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Cost Category Summary */}
        <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t">
          <div className="text-center">
            <p className="text-xs text-muted-foreground">Fixed Costs</p>
            <p className="text-sm font-semibold">
              {formatCurrency(
                tcoResult.monthly_mortgage +
                  tcoResult.monthly_property_tax +
                  tcoResult.monthly_insurance +
                  tcoResult.monthly_hoa
              )}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-muted-foreground">Variable Costs</p>
            <p className="text-sm font-semibold">
              {formatCurrency(tcoResult.monthly_utilities + tcoResult.monthly_maintenance)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-muted-foreground">Discretionary</p>
            <p className="text-sm font-semibold">
              {formatCurrency(tcoResult.monthly_internet + tcoResult.monthly_parking)}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
