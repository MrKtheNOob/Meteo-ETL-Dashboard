import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend
} from 'recharts';
import { WeatherData } from '../types/weather';

interface WeatherConditionsChartProps {
  data: WeatherData[];
  loading?: boolean;
}

const WeatherConditionsChart: React.FC<WeatherConditionsChartProps> = ({ data, loading = false }) => {
  if (loading) {
    return (
      <div className="chart-card">
        <div className="chart-title">Weather Conditions Distribution</div>
        <div className="loading">Loading weather conditions data...</div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="chart-card">
        <div className="chart-title">Weather Conditions Distribution</div>
        <div className="loading">No weather conditions data available</div>
      </div>
    );
  }

  // Count weather conditions
  const conditionCounts = data.reduce((acc, item) => {
    const condition = item.condition?.texte_condition || 'Unknown';
    acc[condition] = (acc[condition] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // Transform to chart data format
  const chartData = Object.entries(conditionCounts).map(([name, value]) => ({
    name,
    value
  }));

  // Colors for different weather conditions
  const COLORS = [
    '#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8',
    '#82CA9D', '#FFC658', '#FF7300', '#8DD1E1', '#D084D0'
  ];

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div style={{
          backgroundColor: 'white',
          padding: '10px',
          border: '1px solid #ccc',
          borderRadius: '5px'
        }}>
          <p style={{ margin: 0, color: payload[0].payload.fill }}>
            {`${payload[0].name}: ${payload[0].value} observations`}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="chart-card">
      <div className="chart-title">Weather Conditions Distribution</div>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

export default WeatherConditionsChart; 