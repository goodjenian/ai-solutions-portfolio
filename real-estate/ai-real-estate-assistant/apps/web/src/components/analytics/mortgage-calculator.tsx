"use client";

import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { calculateMortgage, calculateTCO, ApiError } from "@/lib/api";
import { MortgageResult, TCOResult } from "@/lib/types";
import { Loader2, AlertCircle, RefreshCw, Calculator, ChevronDown, ChevronUp, Scale, Download } from "lucide-react";
import { TCOBreakdownChart } from "./charts/tco-breakdown-chart";
import { TCOComparison } from "./tco-comparison";
import { exportTCOToPDF } from "@/lib/pdf-export";

interface ErrorState {
  message: string;
  requestId?: string;
}

const extractErrorState = (err: unknown): ErrorState => {
  let message = "Unknown error";
  let requestId: string | undefined = undefined;

  if (err instanceof ApiError) {
    message = err.message;
    requestId = err.request_id;
  } else if (err instanceof Error) {
    message = err.message;
  } else {
    message = String(err);
  }

  return { message, requestId };
};

export function MortgageCalculator() {
  const [loading, setLoading] = useState(false);
  const [errorState, setErrorState] = useState<ErrorState | null>(null);
  const [result, setResult] = useState<MortgageResult | null>(null);
  const [tcoResult, setTcoResult] = useState<TCOResult | null>(null);
  const [lastFormData, setLastFormData] = useState<typeof formData | null>(null);
  const [showTcoOptions, setShowTcoOptions] = useState(false);
  const [showComparison, setShowComparison] = useState(false);

  const [formData, setFormData] = useState({
    property_price: 500000,
    down_payment_percent: 20,
    interest_rate: 4.5,
    loan_years: 30,
    // TCO fields
    monthly_hoa: 0,
    annual_property_tax: 0,
    annual_insurance: 0,
    monthly_utilities: 0,
    monthly_internet: 0,
    monthly_parking: 0,
    maintenance_percent: 1,
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: parseFloat(value) || 0,
    }));
  };

  const handleCalculate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorState(null);
    setLastFormData(formData);

    try {
      const [mortgageData, tcoData] = await Promise.all([
        calculateMortgage(formData),
        calculateTCO(formData),
      ]);
      setResult(mortgageData);
      setTcoResult(tcoData);
    } catch (err: unknown) {
      setErrorState(extractErrorState(err));
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = async () => {
    if (!lastFormData || loading) return;
    setLoading(true);
    setErrorState(null);

    try {
      const [mortgageData, tcoData] = await Promise.all([
        calculateMortgage(lastFormData),
        calculateTCO(lastFormData),
      ]);
      setResult(mortgageData);
      setTcoResult(tcoData);
    } catch (err: unknown) {
      setErrorState(extractErrorState(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid gap-6 md:grid-cols-2">
      {/* STATE 1: Empty state - guidance before calculation */}
      {!result && !errorState && !loading && (
        <div
          className="col-span-full md:col-span-2 rounded-lg border bg-muted/30 p-6 text-center"
          role="status"
          aria-live="polite"
        >
          <div className="flex justify-center mb-3">
            <div className="p-3 rounded-full bg-primary/10">
              <Calculator className="h-8 w-8 text-primary" aria-hidden="true" />
            </div>
          </div>
          <h3 className="text-lg font-semibold mb-2">Mortgage Calculator</h3>
          <p className="text-sm text-muted-foreground max-w-md mx-auto mb-3">
            Enter your property details below to estimate monthly payments, total interest, and complete loan breakdown.
          </p>
          <p className="text-xs text-muted-foreground">
            Adjust the default values and click Calculate to see your personalized mortgage analysis.
          </p>
        </div>
      )}

      {/* Calculator Form */}
      <Card>
        <CardHeader>
          <CardTitle>Mortgage Calculator</CardTitle>
          <CardDescription>
            Estimate your monthly payments and total costs.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCalculate} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="property_price">Property Price ($)</Label>
              <Input
                id="property_price"
                name="property_price"
                type="number"
                value={formData.property_price}
                onChange={handleChange}
                min="0"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="down_payment_percent">Down Payment (%)</Label>
              <Input
                id="down_payment_percent"
                name="down_payment_percent"
                type="number"
                value={formData.down_payment_percent}
                onChange={handleChange}
                min="0"
                max="100"
                step="0.1"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="interest_rate">Interest Rate (%)</Label>
              <Input
                id="interest_rate"
                name="interest_rate"
                type="number"
                value={formData.interest_rate}
                onChange={handleChange}
                min="0"
                step="0.01"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="loan_years">Loan Term (Years)</Label>
              <Input
                id="loan_years"
                name="loan_years"
                type="number"
                value={formData.loan_years}
                onChange={handleChange}
                min="1"
                max="50"
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Calculate
            </Button>

            {/* TCO Options Toggle */}
            <Button
              type="button"
              variant="outline"
              className="w-full"
              onClick={() => setShowTcoOptions(!showTcoOptions)}
            >
              {showTcoOptions ? (
                <>
                  <ChevronUp className="mr-2 h-4 w-4" />
                  Hide Total Cost of Ownership Options
                </>
              ) : (
                <>
                  <ChevronDown className="mr-2 h-4 w-4" />
                  Add Total Cost of Ownership (Utilities, Taxes, etc.)
                </>
              )}
            </Button>

            {/* TCO Input Fields */}
            {showTcoOptions && (
              <div className="space-y-4 pt-4 border-t">
                <h4 className="text-sm font-semibold">Total Cost of Ownership Options</h4>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="monthly_hoa">Monthly HOA ($)</Label>
                    <Input
                      id="monthly_hoa"
                      name="monthly_hoa"
                      type="number"
                      value={formData.monthly_hoa}
                      onChange={handleChange}
                      min="0"
                      step="0.01"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="annual_property_tax">Annual Property Tax ($)</Label>
                    <Input
                      id="annual_property_tax"
                      name="annual_property_tax"
                      type="number"
                      value={formData.annual_property_tax}
                      onChange={handleChange}
                      min="0"
                      step="0.01"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="annual_insurance">Annual Insurance ($)</Label>
                    <Input
                      id="annual_insurance"
                      name="annual_insurance"
                      type="number"
                      value={formData.annual_insurance}
                      onChange={handleChange}
                      min="0"
                      step="0.01"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="monthly_utilities">Monthly Utilities ($)</Label>
                    <Input
                      id="monthly_utilities"
                      name="monthly_utilities"
                      type="number"
                      value={formData.monthly_utilities}
                      onChange={handleChange}
                      min="0"
                      step="0.01"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="monthly_internet">Monthly Internet ($)</Label>
                    <Input
                      id="monthly_internet"
                      name="monthly_internet"
                      type="number"
                      value={formData.monthly_internet}
                      onChange={handleChange}
                      min="0"
                      step="0.01"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="monthly_parking">Monthly Parking ($)</Label>
                    <Input
                      id="monthly_parking"
                      name="monthly_parking"
                      type="number"
                      value={formData.monthly_parking}
                      onChange={handleChange}
                      min="0"
                      step="0.01"
                    />
                  </div>
                  <div className="space-y-2 col-span-2">
                    <Label htmlFor="maintenance_percent">Annual Maintenance (% of property value)</Label>
                    <Input
                      id="maintenance_percent"
                      name="maintenance_percent"
                      type="number"
                      value={formData.maintenance_percent}
                      onChange={handleChange}
                      min="0"
                      max="5"
                      step="0.1"
                    />
                    <p className="text-xs text-muted-foreground">
                      Common rule: 1-2% of property value per year for maintenance
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* STATE 3: Error state with request_id and retry */}
            {errorState && (
              <div
                className="flex flex-col items-start gap-3 rounded-lg border border-destructive/20 bg-destructive/10 p-4"
                role="alert"
                aria-live="assertive"
              >
                <div className="flex items-start gap-2">
                  <AlertCircle className="h-4 w-4 text-destructive mt-0.5 shrink-0" aria-hidden="true" />
                  <div className="flex-1">
                    <p className="text-sm text-destructive font-medium">Calculation failed</p>
                    <p className="text-sm text-destructive/90 mt-1">{errorState.message}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 w-full">
                  {errorState.requestId && (
                    <p className="text-xs text-muted-foreground font-mono">
                      request_id={errorState.requestId}
                    </p>
                  )}
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleRetry}
                    disabled={loading}
                    className="gap-2 ml-auto"
                  >
                    <RefreshCw className="h-3 w-3" />
                    Retry
                  </Button>
                </div>
              </div>
            )}
          </form>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Mortgage Results</CardTitle>
            <CardDescription>
              Breakdown of your estimated mortgage.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Monthly Payment</p>
                <p className="text-2xl font-bold">
                  ${result.monthly_payment.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Down Payment</p>
                <p className="text-xl font-semibold">
                  ${result.down_payment.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Interest</p>
                <p className="text-lg">
                  ${result.total_interest.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Cost</p>
                <p className="text-lg">
                  ${result.total_cost.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>
              </div>
            </div>

            <div className="border-t pt-4">
              <h4 className="text-sm font-medium mb-2">Monthly Breakdown</h4>
              <div className="space-y-1">
                {Object.entries(result.breakdown).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-sm">
                    <span className="capitalize">{key.replace(/_/g, " ")}</span>
                    <span>${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {tcoResult && (
        <Card className="col-span-full md:col-span-2">
          <CardHeader>
            <CardTitle>Total Cost of Ownership</CardTitle>
            <CardDescription>
              Complete monthly and annual costs including mortgage, taxes, insurance, utilities, and maintenance.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Monthly TCO Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-primary/5 rounded-lg p-3">
                <p className="text-xs text-muted-foreground">Monthly TCO</p>
                <p className="text-xl font-bold text-primary">
                  ${tcoResult.monthly_tco.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>
              </div>
              <div className="bg-muted rounded-lg p-3">
                <p className="text-xs text-muted-foreground">Annual TCO</p>
                <p className="text-lg font-semibold">
                  ${tcoResult.annual_tco.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>
              </div>
              <div className="bg-muted rounded-lg p-3">
                <p className="text-xs text-muted-foreground">Total Over {formData.loan_years} Years</p>
                <p className="text-lg font-semibold">
                  ${tcoResult.total_ownership_cost.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>
              </div>
              <div className="bg-muted rounded-lg p-3">
                <p className="text-xs text-muted-foreground">All-In Cost</p>
                <p className="text-lg font-semibold">
                  ${tcoResult.total_all_costs.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>
              </div>
            </div>

            {/* Monthly Breakdown */}
            <div className="border-t pt-4">
              <h4 className="text-sm font-medium mb-3">Monthly Cost Breakdown</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="flex justify-between text-sm p-2 bg-muted/50 rounded">
                  <span className="text-muted-foreground">Mortgage</span>
                  <span className="font-medium">${tcoResult.monthly_mortgage.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
                <div className="flex justify-between text-sm p-2 bg-muted/50 rounded">
                  <span className="text-muted-foreground">Property Tax</span>
                  <span className="font-medium">${tcoResult.monthly_property_tax.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
                <div className="flex justify-between text-sm p-2 bg-muted/50 rounded">
                  <span className="text-muted-foreground">Insurance</span>
                  <span className="font-medium">${tcoResult.monthly_insurance.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
                <div className="flex justify-between text-sm p-2 bg-muted/50 rounded">
                  <span className="text-muted-foreground">HOA</span>
                  <span className="font-medium">${tcoResult.monthly_hoa.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
                <div className="flex justify-between text-sm p-2 bg-muted/50 rounded">
                  <span className="text-muted-foreground">Utilities</span>
                  <span className="font-medium">${tcoResult.monthly_utilities.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
                <div className="flex justify-between text-sm p-2 bg-muted/50 rounded">
                  <span className="text-muted-foreground">Internet</span>
                  <span className="font-medium">${tcoResult.monthly_internet.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
                <div className="flex justify-between text-sm p-2 bg-muted/50 rounded">
                  <span className="text-muted-foreground">Parking</span>
                  <span className="font-medium">${tcoResult.monthly_parking.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
                <div className="flex justify-between text-sm p-2 bg-muted/50 rounded">
                  <span className="text-muted-foreground">Maintenance</span>
                  <span className="font-medium">${tcoResult.monthly_maintenance.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* TCO Breakdown Pie Chart */}
      {tcoResult && (
        <TCOBreakdownChart
          tcoResult={tcoResult}
          className="col-span-full md:col-span-2"
        />
      )}

      {/* Export PDF Button */}
      {tcoResult && (
        <div className="col-span-full md:col-span-2 flex justify-center">
          <Button
            variant="outline"
            onClick={() => exportTCOToPDF(tcoResult)}
            className="gap-2"
          >
            <Download className="h-4 w-4" />
            Export to PDF
          </Button>
        </div>
      )}

      {/* Compare Scenarios Button */}
      {tcoResult && (
        <div className="col-span-full md:col-span-2 flex justify-center">
          <Button
            variant="outline"
            size="lg"
            onClick={() => setShowComparison(!showComparison)}
            className="gap-2"
          >
            <Scale className="h-4 w-4" />
            {showComparison ? "Hide Comparison" : "Compare Scenarios"}
          </Button>
        </div>
      )}

      {/* TCO Comparison Section */}
      {showComparison && (
        <div className="col-span-full md:col-span-2">
          <TCOComparison />
        </div>
      )}
    </div>
  );
}
