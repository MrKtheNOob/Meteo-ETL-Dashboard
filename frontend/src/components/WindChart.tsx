import React from 'react';
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Bar
} from 'recharts';
import { WindData } from '../types/weather';

interface WindChartProps {
  data: WindData[];
  loading?: boolean;
}

const WindChart: React.FC<WindChartProps> = ({ data, loading = false }) => {
  if (loading) {
    return (
      <div className="chart-card">
        <div className="chart-title">Wind Data</div>
        <div className="loading">Loading wind data...</div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="chart-card">
        <div className="chart-title">Wind Data</div>
        <div className="loading">No wind data available</div>
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
            {`Wind Speed: ${payload[0].value} km/h`}
          </p>
          <p style={{ margin: 0, color: '#ffc658' }}>
            {`Gusts: ${payload[1].value} km/h`}
          </p>
          <p style={{ margin: 0 }}>
            {`Direction: ${payload[2]?.payload?.windDirection || 'N/A'}`}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="chart-card">
      <div className="chart-title">Wind Speed & Gusts (km/h)</div>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="date" 
            tickFormatter={formatDate}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis 
            label={{ value: 'Speed (km/h)', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Bar dataKey="windSpeed" fill="#ff7300" name="Wind Speed" />
          <Line type="monotone" dataKey="gusts" stroke="#ffc658" name="Wind Gusts" strokeWidth={2} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

export default WindChart; 