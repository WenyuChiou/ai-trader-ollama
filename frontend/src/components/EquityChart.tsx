import React, { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface EquityRecord {
  date: string;
  total_value: number;
  total_pnl: number;
  total_pnl_pct: number;
  equity_value: number;
  cash: number;
}

interface EquityChartProps {
  data?: EquityRecord[];
  height?: number;
}

const EquityChart: React.FC<EquityChartProps> = ({ data = [], height = 400 }) => {
  if (!data || data.length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
        No equity history data available. Run trading cycles to see the chart.
      </div>
    );
  }

  // Format data for chart (convert dates and format values)
  const chartData = data.map((record) => ({
    date: record.date.substring(5), // YYYY-MM-DD -> MM-DD
    totalValue: parseFloat(record.total_value.toFixed(2)),
    totalPnl: parseFloat(record.total_pnl.toFixed(2)),
    totalPnlPct: parseFloat(record.total_pnl_pct.toFixed(2)),
    equityValue: parseFloat(record.equity_value.toFixed(2)),
    cash: parseFloat(record.cash.toFixed(2)),
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis yAxisId="left" />
        <YAxis yAxisId="right" orientation="right" />
        <Tooltip
          formatter={(value: number, name: string) => {
            if (name === 'totalValue' || name === 'equityValue' || name === 'cash') {
              return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            }
            if (name === 'totalPnlPct') {
              return `${value.toFixed(2)}%`;
            }
            return `$${value.toFixed(2)}`;
          }}
        />
        <Legend />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="totalValue"
          stroke="#8884d8"
          strokeWidth={2}
          name="Total Value"
          dot={{ r: 4 }}
          activeDot={{ r: 6 }}
        />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="equityValue"
          stroke="#82ca9d"
          strokeWidth={2}
          name="Equity Value"
          dot={{ r: 3 }}
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="totalPnlPct"
          stroke="#ffc658"
          strokeWidth={2}
          name="Total P&L %"
          dot={{ r: 3 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default EquityChart;

