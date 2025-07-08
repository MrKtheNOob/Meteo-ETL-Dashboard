import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { TemperatureData } from '../types/weather';

interface TemperatureChartProps {
  data: TemperatureData[];
  loading?: boolean;
}

const TemperatureChart: React.FC<TemperatureChartProps> = ({ data, loading = false }) => {
  if (loading) {
    return (
      <div className="chart-card">
        <div className="chart-title">Temperature Trends</div>
        <div className="loading">Loading temperature data...</div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="chart-card">
        <div className="chart-title">Temperature Trends</div>
        <div className="loading">No temperature data available</div>
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
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
          <p style={{ margin: 0, color: '#8884d8' }}>
            {`Temperature: ${payload[0].value}°C`}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="chart-card">
      <div className="chart-title">Temperature Trends (°C)</div>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="date" 
            tickFormatter={formatDate}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis 
            domain={['dataMin - 5', 'dataMax + 5']}
            label={{ value: 'Temperature (°C)', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Area
            type="monotone"
            dataKey="temperature"
            stroke="#8884d8"
            fill="#8884d8"
            fillOpacity={0.3}
            name="Temperature"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TemperatureChart; 