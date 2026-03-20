import React, { useState } from 'react';

interface ReportViewerProps {
  report: Record<string, any> | null;
}

type Tab = 'json' | 'markdown' | 'metadata';

const MetaRow = ({ label, value }: { label: string; value: React.ReactNode }) => (
  <tr className="border-b last:border-0 hover:bg-gray-50">
    <td className="py-2 pr-6 font-medium text-gray-500 text-sm whitespace-nowrap w-52">{label}</td>
    <td className="py-2 text-gray-800 text-sm break-all">{value ?? <span className="text-gray-400 italic">N/A</span>}</td>
  </tr>
);

function buildMarkdown(report: Record<string, any>): string {
  const h  = report.engines?.harmonic?.metrics;
  const s34  = h?.['34_stats']  ?? {};
  const s134 = h?.['134_stats'] ?? {};
  return [
    `# OMEGA Analysis Report`,
    ``,
    `| Campo | Valor |`,
    `|---|---|`,
    `| **Ativo** | ${report.asset ?? 'N/A'} |`,
    `| **Timeframe** | ${report.timeframe ?? 'N/A'} |`,
    `| **Status** | ${report.status ?? 'N/A'} |`,
    `| **Agente** | ${report.agent_version ?? 'N/A'} |`,
    `| **Criado em** | ${report.created_at ?? 'N/A'} |`,
    ``,
    `## Métricas Harmônicas`,
    ``,
    `| Nível | Toques | HIT | BREAK | Hit Rate |`,
    `|---|---|---|---|---|`,
    `| EMA-34  | ${s34.total_touches ?? 0} | ${s34.hits ?? 0} | ${s34.breaks ?? 0} | ${s34.hit_rate ?? 0}% |`,
    `| EMA-134 | ${s134.total_touches ?? 0} | ${s134.hits ?? 0} | ${s134.breaks ?? 0} | ${s134.hit_rate ?? 0}% |`,
    ``,
    `## Integridade Criptográfica`,
    `\`\`\``,
    `SHA3-256 (JSON Output): ${report.checksum ?? 'N/A'}`,
    `SHA3-256 (linha.csv):   ${report.checksum_sources?.linha ?? 'N/A'}`,
    `SHA3-256 (candle.csv):  ${report.checksum_sources?.candle ?? 'N/A'}`,
    `\`\`\``,
  ].join('\n');
}

function downloadBlob(content: string, filename: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export const ReportViewer: React.FC<ReportViewerProps> = ({ report }) => {
  const [tab, setTab] = useState<Tab>('json');

  if (!report) {
    return <div className="text-gray-400 text-sm p-4 border rounded">Nenhum relatório selecionado.</div>;
  }

  const jsonStr = JSON.stringify(report, null, 2);
  const mdStr   = buildMarkdown(report);
  const sym     = report.asset ?? 'UNKNOWN';
  const tf      = report.timeframe ?? 'XX';

  const tabCls = (t: Tab) =>
    `px-4 py-2 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
      tab === t ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500 hover:text-gray-700'
    }`;

  const h = report.engines?.harmonic?.metrics;

  return (
    <div className="border rounded-lg shadow-sm bg-white overflow-hidden mt-4">
      {/* Header */}
      <div className="flex items-center justify-between px-4 pt-3 bg-gray-50 border-b">
        <div className="flex gap-1">
          {(['json', 'markdown', 'metadata'] as Tab[]).map(t => (
            <button key={t} className={tabCls(t)} onClick={() => setTab(t)}>
              {t === 'json' ? 'JSON' : t === 'markdown' ? 'Markdown' : 'Metadata'}
            </button>
          ))}
        </div>
        <div className="flex gap-2 pb-2">
          <button
            onClick={() => downloadBlob(jsonStr, `report_${sym}_${tf}.json`, 'application/json')}
            className="text-xs px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">
            ⬇ JSON
          </button>
          <button
            onClick={() => downloadBlob(mdStr, `report_${sym}_${tf}.md`, 'text/markdown')}
            className="text-xs px-3 py-1 bg-gray-700 text-white rounded hover:bg-gray-800">
            ⬇ MD
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {tab === 'json' && (
          <pre className="text-xs bg-gray-950 text-green-400 p-4 rounded-lg overflow-auto max-h-[500px] leading-relaxed">
            {jsonStr}
          </pre>
        )}

        {tab === 'markdown' && (
          <div className="prose max-w-none text-sm bg-gray-50 p-4 rounded-lg max-h-[500px] overflow-auto whitespace-pre-wrap font-mono">
            {mdStr}
          </div>
        )}

        {tab === 'metadata' && (
          <table className="w-full border-collapse">
            <tbody>
              <MetaRow label="Status"            value={<span className={`font-bold ${report.status === 'COMPLETED' ? 'text-green-600' : 'text-red-600'}`}>{report.status}</span>} />
              <MetaRow label="Ativo"             value={report.asset} />
              <MetaRow label="Timeframe"         value={report.timeframe} />
              <MetaRow label="Agente"            value={report.agent_version} />
              <MetaRow label="Omega Integration" value={String(report.omega_integration ?? false)} />
              <MetaRow label="Criado em"         value={report.created_at} />
              <MetaRow label="Hit Rate EMA-34"   value={h?.['34_stats']?.hit_rate  != null ? `${h['34_stats'].hit_rate}%`  : 'N/A'} />
              <MetaRow label="Hit Rate EMA-134"  value={h?.['134_stats']?.hit_rate != null ? `${h['134_stats'].hit_rate}%` : 'N/A'} />
              <MetaRow label="Eventos Totais"    value={report.engines?.harmonic?.events?.length ?? 0} />
              <MetaRow label="confidence_score"  value={report.confidence_score} />
              <MetaRow label="mach_number"       value={report.mach_number} />
              <MetaRow label="flutter_risk"      value={report.flutter_risk} />
              <MetaRow label="dominant_cycle"    value={report.dominant_cycle} />
              <MetaRow label="trajectory_phase"  value={report.trajectory_phase} />
              <MetaRow label="data_points"       value={report.data_points} />
              <MetaRow label="period"            value={report.period} />
              <MetaRow label="mission_id"        value={report.mission_id} />
              <MetaRow label="Checksum (SHA3-256)" value={<span className="font-mono text-xs break-all text-blue-700">{report.checksum}</span>} />
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
