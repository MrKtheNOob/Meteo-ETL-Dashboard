import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { PrecipitationData } from '../types/weather';

interface PrecipitationChartProps {
  data: PrecipitationData[];
  loading?: boolean;
}

const PrecipitationChart: React.FC<PrecipitationChartProps> = ({ data, loading = false }) => {
  if (loading) {
    return (
      <div className="chart-card">
        <div className="chart-title">Precipitation Data</div>
        <div className="loading">Loading precipitation data...</div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="chart-card">
        <div className="chart-title">Precipitation Data</div>
        <div className="loading">No precipitation data available</div>
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
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
          <p style={{ margin: 0, color: '#82ca9d' }}>
            {`Precipitation: ${payload[0].value} mm`}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="chart-card">
      <div className="chart-title">Precipitation (mm)</div>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="date" 
            tickFormatter={formatDate}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis 
            label={{ value: 'Precipitation (mm)', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Bar dataKey="precipitation" fill="#82ca9d" name="Precipitation" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PrecipitationChart; 