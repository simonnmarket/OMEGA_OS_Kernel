import React, { useState, useCallback } from 'react';

interface DataInputPanelProps {
  onDataLoaded?: (type: 'linha' | 'candle', rows: number) => void;
}

const REQUIRED_LINHA  = ['time', 'linha'];
const REQUIRED_CANDLE_PRIMARY  = ['time', 'open', 'high', 'low', 'close', 'tick_volume'];
const REQUIRED_CANDLE_FALLBACK = ['time', 'open', 'high', 'low', 'close', 'volume'];

function detectType(headers: string[]): 'linha' | 'candle' | null {
  if (REQUIRED_LINHA.every(c => headers.includes(c))) return 'linha';
  if (
    REQUIRED_CANDLE_PRIMARY.every(c => headers.includes(c)) ||
    REQUIRED_CANDLE_FALLBACK.every(c => headers.includes(c))
  ) return 'candle';
  return null;
}

export const DataInputPanel: React.FC<DataInputPanelProps> = ({ onDataLoaded }) => {
  const [messages, setMessages] = useState<{ type: 'ok' | 'error'; text: string }[]>([]);

  const processFile = useCallback((file: File) => {
    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = (ev.target?.result as string) ?? '';
      const lines = text.split('\n').filter(l => l.trim() !== '');
      if (lines.length < 2) {
        setMessages(m => [...m, { type: 'error', text: `❌ ${file.name}: arquivo vazio ou sem dados.` }]);
        return;
      }
      const headers = lines[0].toLowerCase().replace(/\r/g, '').split(',');
      const csvType = detectType(headers);
      if (!csvType) {
        setMessages(m => [...m, {
          type: 'error',
          text: `❌ ${file.name}: Schema inválido. Colunas encontradas: [${headers.join(', ')}]. ` +
                `Exigido: [${REQUIRED_LINHA.join(', ')}] ou [${REQUIRED_CANDLE_PRIMARY.join(', ')}].`
        }]);
        return;
      }
      const rowCount = lines.length - 1;
      setMessages(m => [...m, { type: 'ok', text: `✅ ${file.name} — Tipo: ${csvType.toUpperCase()} | ${rowCount} linhas validadas.` }]);
      onDataLoaded?.(csvType, rowCount);
    };
    reader.readAsText(file);
  }, [onDataLoaded]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setMessages([]);
    Array.from(e.target.files ?? []).forEach(processFile);
  };

  return (
    <div className="p-4 border rounded-lg shadow-sm bg-white mb-4">
      <h3 className="text-lg font-semibold text-gray-800 mb-1">📂 Data Input Panel</h3>
      <p className="text-xs text-gray-500 mb-3">
        Aceita CSV de <code>grafico_linha</code> (time, linha) e <code>grafico_candle</code> (OHLCV).
      </p>
      <input
        id="csv-input"
        type="file"
        accept=".csv"
        multiple
        onChange={handleChange}
        className="block text-sm file:mr-3 file:py-1 file:px-3 file:rounded file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
      />
      <div className="mt-3 space-y-1">
        {messages.map((m, i) => (
          <p key={i} className={`text-xs font-medium px-2 py-1 rounded ${m.type === 'error' ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
            {m.text}
          </p>
        ))}
      </div>
    </div>
  );
};
