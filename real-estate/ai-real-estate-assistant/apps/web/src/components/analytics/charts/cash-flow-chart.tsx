'use client';

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import type { YearlyCashFlow } from '@/lib/types';

interface CashFlowChartProps {
  data: YearlyCashFlow[];
  title?: string;
  description?: string;
  className?: string;
}

export function CashFlowChart({
  data,
  title = 'Cash Flow Projection',
  description = 'Yearly cash flow and cumulative returns',
  className,
}: CashFlowChartProps) {
  const chartData = data.map((item) => ({
    year: `Year ${item.year}`,
    cashFlow: item.cash_flow,
    cumulativeCashFlow: item.cumulative_cash_flow,
    equity: item.equity,
    propertyValue: item.property_value,
  }));

  const formatCurrency = (value: number) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    }
    return `$${(value / 1000).toFixed(0)}K`;
  };

  const totalCashFlow = data.length > 0 ? data[data.length - 1].cumulative_cash_flow : 0;
  const finalEquity = data.length > 0 ? data[data.length - 1].equity : 0;

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" tick={{ fontSize: 11 }} tickLine={false} />
              <YAxis tick={{ fontSize: 11 }} tickLine={false} tickFormatter={formatCurrency} />
              <Tooltip
                formatter={(value: number, name: string) => [
                  `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`,
                  name === 'cashFlow'
                    ? 'Annual Cash Flow'
                    : name === 'cumulativeCashFlow'
                      ? 'Cumulative Cash Flow'
                      : name === 'equity'
                        ? 'Equity'
                        : 'Property Value',
                ]}
              />
              <Legend />
              <Area
                type="monotone"
                dataKey="cumulativeCashFlow"
                stackId="1"
                stroke="#22c55e"
                fill="#22c55e"
                fillOpacity={0.3}
                name="Cumulative Cash Flow"
              />
              <Area
                type="monotone"
                dataKey="equity"
                stackId="2"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.3}
                name="Equity"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Summary */}
        <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t">
          <div>
            <p className="text-sm text-muted-foreground">Total Cash Flow</p>
            <p
              className={`text-lg font-semibold ${totalCashFlow >= 0 ? 'text-green-600' : 'text-red-600'}`}
            >
              ${totalCashFlow.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Final Equity</p>
            <p className="text-lg font-semibold text-blue-600">
              ${finalEquity.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
