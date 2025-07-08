import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { WeatherData } from '../types/weather';

interface PressureChartProps {
  data: WeatherData[];
  loading?: boolean;
}

const PressureChart: React.FC<PressureChartProps> = ({ data, loading = false }) => {
  if (loading) {
    return (
      <div className="chart-card">
        <div className="chart-title">Atmospheric Pressure</div>
        <div className="loading">Loading pressure data...</div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="chart-card">
        <div className="chart-title">Atmospheric Pressure</div>
        <div className="loading">No pressure data available</div>
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit'
    });
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div style={{
          backgroundColor: 'white',
          padding: '10px',
          border: '1px solid #ccc',
          borderRadius: '5px'
        }}>
          <p style={{ margin: 0 }}>{`Date: ${formatDate(label)}`}</p>
          <p style={{ margin: 0, color: '#ff7300' }}>
            {`Pressure: ${payload[0].value} mb`}
          </p>
        </div>
      );
    }
    return null;
  };

  // Transform data for the chart
  const chartData = data.map(item => ({
    date: item.temps?.date || new Date().toISOString(),
    pressure: item.pression_millibars
  }));

  return (
    <div className="chart-card">
      <div className="chart-title">Atmospheric Pressure (mb)</div>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="date" 
            tickFormatter={formatDate}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis 
            label={{ value: 'Pressure (mb)', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="pressure" 
            stroke="#ff7300" 
            name="Pressure" 
            strokeWidth={2}
            dot={{ fill: '#ff7300', strokeWidth: 2, r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PressureChart; 