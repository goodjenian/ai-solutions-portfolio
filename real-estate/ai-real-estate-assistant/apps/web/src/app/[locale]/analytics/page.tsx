import { BarChart3, TrendingUp, Calculator, PieChart, Scale } from 'lucide-react';
import { MortgageCalculator } from '@/components/analytics/mortgage-calculator';
import { InvestmentAnalyzer } from '@/components/analytics/investment-analyzer';
import { AdvancedInvestmentAnalyzer } from '@/components/analytics/advanced-investment-analyzer';
import { PortfolioAnalyzer } from '@/components/analytics/portfolio-analyzer';
import { RentVsBuyCalculator } from '@/components/analytics/rent-vs-buy-calculator';

export default function AnalyticsPage() {
  return (
    <div className="container py-8 space-y-8">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">Analytics & Tools</h1>
        <p className="text-muted-foreground text-lg">
          Market insights and financial tools to help you make informed decisions.
        </p>
      </div>

      <div className="grid gap-8">
        <section>
          <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
            <BarChart3 className="h-6 w-6" />
            Mortgage Calculator
          </h2>
          <MortgageCalculator />
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="h-6 w-6" />
            Investment Property Analyzer
          </h2>
          <InvestmentAnalyzer />
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
            <Calculator className="h-6 w-6" />
            Advanced Investment Analytics
          </h2>
          <AdvancedInvestmentAnalyzer />
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
            <PieChart className="h-6 w-6" />
            Portfolio Analyzer
          </h2>
          <PortfolioAnalyzer />
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
            <Scale className="h-6 w-6" />
            Rent vs Buy Calculator
          </h2>
          <RentVsBuyCalculator />
        </section>
      </div>
    </div>
  );
}
