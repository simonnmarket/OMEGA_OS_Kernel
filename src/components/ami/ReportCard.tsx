import React from 'react';

interface HarmonicStats {
  total_touches: number;
  hits: number;
  breaks: number;
  hit_rate: number;
  break_rate: number;
}

interface ReportCardProps {
  report: {
    asset: string;
    timeframe: string;
    status: 'PENDING' | 'COMPLETED' | 'FAILED';
    created_at?: string;
    agent_version?: string;
    checksum?: string;
    engines?: {
      harmonic?: {
        metrics?: {
          '34_stats'?: HarmonicStats;
          '134_stats'?: HarmonicStats;
        };
        events?: any[];
      };
    };
  };
  onClick?: () => void;
  isActive?: boolean;
}

const StatusBadge = ({ status }: { status: string }) => {
  const colors: Record<string, string> = {
    COMPLETED: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    FAILED:    'bg-red-100 text-red-700 border-red-200',
    PENDING:   'bg-amber-100 text-amber-700 border-amber-200',
  };
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${colors[status] ?? 'bg-gray-100 text-gray-600'}`}>
      {status}
    </span>
  );
};

export const ReportCard: React.FC<ReportCardProps> = ({ report, onClick, isActive }) => {
  const s134 = report.engines?.harmonic?.metrics?.['134_stats'];
  const eventsCount = report.engines?.harmonic?.events?.length ?? 0;

  return (
    <div
      onClick={onClick}
      className={`border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md ${
        isActive ? 'border-blue-500 bg-blue-50 shadow-md' : 'border-gray-200 bg-white hover:border-blue-300'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <span className="text-lg font-bold text-gray-900">{report.asset}</span>
          <span className="text-sm text-gray-500 font-medium bg-gray-100 px-2 py-0.5 rounded">
            {report.timeframe}
          </span>
        </div>
        <StatusBadge status={report.status} />
      </div>

      {s134 && (
        <div className="flex gap-4 mt-2 text-sm">
          <div>
            <span className="text-gray-500">Hit Rate 134: </span>
            <span className={`font-bold ${s134.hit_rate >= 95 ? 'text-emerald-600' : s134.hit_rate >= 75 ? 'text-amber-600' : 'text-red-600'}`}>
              {s134.hit_rate}%
            </span>
          </div>
          <div>
            <span className="text-gray-500">Eventos: </span>
            <span className="font-medium text-gray-700">{eventsCount.toLocaleString()}</span>
          </div>
        </div>
      )}

      {report.created_at && (
        <p className="text-xs text-gray-400 mt-2">
          {new Date(report.created_at).toLocaleString('pt-BR')}
        </p>
      )}

      {report.checksum && (
        <p className="text-xs text-gray-400 font-mono mt-1 truncate" title={report.checksum}>
          SHA3: {report.checksum.slice(0, 20)}…
        </p>
      )}
    </div>
  );
};
