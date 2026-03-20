import React, { useState } from 'react';
import { ReportCard } from '../components/ami/ReportCard';
import { ReportViewer } from '../components/ami/ReportViewer';
import { DataInputPanel } from '../components/ami/DataInputPanel';

// Smoke test report — dados reais do Smoke Test V3 (20/03/2026)
const SMOKE_REPORT = {
  asset: "XAUUSD",
  timeframe: "H1",
  status: "COMPLETED" as const,
  created_at: "2026-03-20T16:38:54Z",
  updated_at: "2026-03-20T16:39:03Z",
  agent_version: "ami_analyzer_v3.0",
  omega_integration: false,
  checksum: "e67cf86d6c4ace6efdd03f91d31cdd834e20c4cc4726af567b6a385272c636ae",
  checksum_sources: {
    linha:  "c5e47c15392ebf2238b59798ead88040870588f0f366baa73f4ee32f4d10219a",
    candle: "7aef6d5ca7e624686479467561bf1c43c58da74d4bab3f03284fb34f37d9b8b8"
  },
  engines: {
    harmonic: {
      metrics: {
        "34_stats":  { total_touches: 24262, hits: 24253, breaks: 9,  hit_rate: 99.96, break_rate: 0.04 },
        "134_stats": { total_touches: 24152, hits: 24148, breaks: 4,  hit_rate: 99.98, break_rate: 0.02 }
      },
      events: [] // eventos completos no CSV/JSON de output
    }
  }
};

export const AMIReports: React.FC = () => {
  const [reports]       = useState([SMOKE_REPORT]);
  const [activeReport, setActiveReport] = useState<typeof SMOKE_REPORT | null>(SMOKE_REPORT);

  return (
    <div className="min-h-screen bg-slate-100">
      {/* Header */}
      <div className="bg-white border-b px-8 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AMI Reports Dashboard</h1>
          <p className="text-sm text-gray-500">Motor Harmônico V3 — SHA3-256 Validated | OMEGA Intelligence OS</p>
        </div>
        <span className="text-xs font-mono bg-emerald-100 text-emerald-700 px-3 py-1 rounded-full border border-emerald-200">
          ami_analyzer_v3.0
        </span>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-6 grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Sidebar */}
        <div className="lg:col-span-1 space-y-4">
          <DataInputPanel onDataLoaded={(type, rows) =>
            console.log(`Loaded ${rows} rows of type ${type}`)
          } />

          <div className="bg-white border rounded-lg p-4">
            <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
              Relatórios ({reports.length})
            </h2>
            <div className="space-y-2">
              {reports.map((r, i) => (
                <ReportCard
                  key={i}
                  report={r}
                  isActive={activeReport === r}
                  onClick={() => setActiveReport(r)}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Main */}
        <div className="lg:col-span-2">
          {activeReport
            ? <ReportViewer report={activeReport} />
            : (
              <div className="flex items-center justify-center h-64 border-2 border-dashed rounded-lg text-gray-400">
                Selecione um relatório para visualizar
              </div>
            )
          }
        </div>
      </div>
    </div>
  );
};
