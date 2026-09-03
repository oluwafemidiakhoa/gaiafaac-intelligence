"use client";

import React, { useState, useEffect } from "react";
import {
  BarChart,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  TrendingDown,
  Eye,
  Lock,
  FileText,
  ArrowRight,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";

interface JurisdictionScore {
  name: string;
  integrity_score: number;
  status: "ready_for_publication" | "ready_for_decisions" | "requires_review" | "not_ready";
  published_claims: number;
  verified_claims: number;
  conflicts: number;
}

interface AnomalyAlert {
  type: string;
  severity: "critical" | "high" | "medium" | "low";
  jurisdiction: string;
  description: string;
  recommendation: string;
}

interface MetricCard {
  label: string;
  value: string;
  change: number;
  status: "up" | "down" | "neutral";
  source_verified: boolean;
}

export function InstitutionalIntelligenceDashboard() {
  const [jurisdictions, setJurisdictions] = useState<JurisdictionScore[]>([]);
  const [anomalies, setAnomalies] = useState<AnomalyAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedJurisdiction, setSelectedJurisdiction] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [readinessRes, riskRes] = await Promise.all([
        fetch("/api/v1/institutional/readiness-matrix"),
        fetch("/api/v1/institutional/risk-indicators"),
      ]);

      if (readinessRes.ok) {
        const data = await readinessRes.json();
        setJurisdictions(data.jurisdictions || []);
      }

      if (riskRes.ok) {
        const data = await riskRes.json();
        setAnomalies(data.critical_risks || []);
      }
    } catch (error) {
      console.error("Failed to fetch institutional data", error);
    } finally {
      setLoading(false);
    }
  };

  const readyCount = jurisdictions.filter(
    (j) => j.status === "ready_for_publication"
  ).length;
  const cautionCount = jurisdictions.filter(
    (j) => j.status === "ready_for_decisions"
  ).length;
  const reviewCount = jurisdictions.filter(
    (j) => j.status === "requires_review"
  ).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">
          Institutional Intelligence & Decision Support
        </h1>
        <p className="text-slate-600 mt-2">
          Comprehensive fiscal data audit, anomaly detection, and institutional readiness
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">
              Ready for Publication
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{readyCount}</div>
            <p className="text-xs text-slate-500 mt-1">
              {readyCount} states verified and ready
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">
              Proceed with Caution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-amber-600">{cautionCount}</div>
            <p className="text-xs text-slate-500 mt-1">
              Review anomalies before decisions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">
              Requires Review
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-600">{reviewCount}</div>
            <p className="text-xs text-slate-500 mt-1">
              Resolve before institutional use
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">
              Total Jurisdictions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">
              {jurisdictions.length}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Under institutional audit
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Critical Anomalies Alert */}
      {anomalies.length > 0 && (
        <Card className="border-red-200 bg-red-50">
          <CardHeader>
            <CardTitle className="text-red-900 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              Critical Institutional Alerts
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {anomalies.map((alert, idx) => (
              <div
                key={idx}
                className="bg-white border border-red-200 rounded-lg p-3 text-sm"
              >
                <div className="flex items-start justify-between mb-1">
                  <div className="font-semibold text-red-900">{alert.type}</div>
                  <Badge
                    variant={
                      alert.severity === "critical"
                        ? "destructive"
                        : "secondary"
                    }
                  >
                    {alert.severity}
                  </Badge>
                </div>
                <p className="text-slate-700 mb-2">{alert.description}</p>
                <p className="text-slate-600 text-xs">
                  <strong>Action:</strong> {alert.recommendation}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Institutional Readiness Matrix */}
      <Card>
        <CardHeader>
          <CardTitle>Institutional Readiness Matrix</CardTitle>
          <CardDescription>
            Which jurisdictions are ready for institutional decisions?
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {jurisdictions.map((jurisdiction) => (
              <div
                key={jurisdiction.name}
                className={`border rounded-lg p-3 cursor-pointer transition-all hover:shadow-md ${
                  jurisdiction.status === "ready_for_publication"
                    ? "border-green-200 bg-green-50"
                    : jurisdiction.status === "ready_for_decisions"
                      ? "border-amber-200 bg-amber-50"
                      : jurisdiction.status === "requires_review"
                        ? "border-red-200 bg-red-50"
                        : "border-slate-200 bg-slate-50"
                }`}
                onClick={() => setSelectedJurisdiction(jurisdiction.name)}
              >
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <div className="font-semibold text-slate-900">
                      {jurisdiction.name}
                    </div>
                    <div className="text-xs text-slate-600">
                      {jurisdiction.published_claims} published •{" "}
                      {jurisdiction.verified_claims} verified
                      {jurisdiction.conflicts > 0
                        ? ` • ${jurisdiction.conflicts} conflicts`
                        : ""}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-slate-900">
                      {jurisdiction.integrity_score}
                    </div>
                    <div className="text-xs text-slate-600">Integrity Score</div>
                  </div>
                </div>

                {/* Status Badge */}
                <div>
                  {jurisdiction.status === "ready_for_publication" && (
                    <Badge className="bg-green-600">
                      <CheckCircle2 className="w-3 h-3 mr-1" />
                      Ready for Publication
                    </Badge>
                  )}
                  {jurisdiction.status === "ready_for_decisions" && (
                    <Badge className="bg-amber-600">
                      <Eye className="w-3 h-3 mr-1" />
                      Ready for Decisions
                    </Badge>
                  )}
                  {jurisdiction.status === "requires_review" && (
                    <Badge variant="destructive">
                      <AlertTriangle className="w-3 h-3 mr-1" />
                      Requires Review
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Selected Jurisdiction Details */}
      {selectedJurisdiction && (
        <Card>
          <CardHeader>
            <CardTitle>{selectedJurisdiction} - Detailed Analysis</CardTitle>
            <CardDescription>
              Decision support analysis and recommendations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Analysis Options */}
              <Button
                onClick={() =>
                  window.open(
                    `/api/v1/decisions/analysis/${selectedJurisdiction}`
                  )
                }
                className="w-full justify-start"
                variant="outline"
              >
                <TrendingUp className="w-4 h-4 mr-2" />
                View Anomaly Analysis
              </Button>

              <Button
                onClick={() =>
                  window.open(
                    `/api/v1/institutional/audit/jurisdiction/${selectedJurisdiction}`
                  )
                }
                className="w-full justify-start"
                variant="outline"
              >
                <Lock className="w-4 h-4 mr-2" />
                View Audit Report
              </Button>

              <Button
                onClick={() =>
                  window.open(
                    `/api/v1/decisions/comparable-analysis/${selectedJurisdiction}/2024-01/revenue`
                  )
                }
                className="w-full justify-start"
                variant="outline"
              >
                <BarChart className="w-4 h-4 mr-2" />
                View Peer Comparison
              </Button>

              <Button
                onClick={() =>
                  window.open(
                    `/api/v1/decisions/decision-packet/${selectedJurisdiction}`
                  )
                }
                className="w-full justify-start"
                variant="outline"
              >
                <FileText className="w-4 h-4 mr-2" />
                Generate Decision Packet
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Key Features */}
      <Card>
        <CardHeader>
          <CardTitle>Institutional Capabilities</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="flex gap-3">
              <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
              <div>
                <div className="font-semibold">Evidence Provenance</div>
                <p className="text-slate-600">Every number linked to source with SHA-256 hash</p>
              </div>
            </div>

            <div className="flex gap-3">
              <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
              <div>
                <div className="font-semibold">Anomaly Detection</div>
                <p className="text-slate-600">AI identifies unusual trends and peer deviations</p>
              </div>
            </div>

            <div className="flex gap-3">
              <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
              <div>
                <div className="font-semibold">Four-Eyes Control</div>
                <p className="text-slate-600">Separate review and approval for institutional compliance</p>
              </div>
            </div>

            <div className="flex gap-3">
              <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
              <div>
                <div className="font-semibold">Decision Packets</div>
                <p className="text-slate-600">Institutional decision support with full audit trail</p>
              </div>
            </div>

            <div className="flex gap-3">
              <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
              <div>
                <div className="font-semibold">Peer Benchmarking</div>
                <p className="text-slate-600">Compare metrics across peer jurisdictions</p>
              </div>
            </div>

            <div className="flex gap-3">
              <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
              <div>
                <div className="font-semibold">Compliance Ready</div>
                <p className="text-slate-600">Complete audit trail and digital signatures</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* API Endpoints Reference */}
      <Card className="bg-slate-50">
        <CardHeader>
          <CardTitle className="text-sm">API Endpoints for Developers</CardTitle>
        </CardHeader>
        <CardContent className="text-xs space-y-2 font-mono">
          <div>GET /api/v1/institutional/readiness-matrix</div>
          <div>GET /api/v1/institutional/risk-indicators</div>
          <div>GET /api/v1/decisions/analysis/{"{jurisdiction}"}</div>
          <div>GET /api/v1/decisions/decision-packet/{"{jurisdiction}"}</div>
          <div>GET /api/v1/evidence/provenance/{"{gaia_id}"}</div>
          <div>GET /api/v1/institutional/audit/complete</div>
        </CardContent>
      </Card>
    </div>
  );
}
