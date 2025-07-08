import React, { useState, useEffect } from 'react';
import { weatherApi } from './services/api';
import { DashboardFilters, WeatherData, TemperatureData, PrecipitationData, WindData, HumidityData } from './types/weather';
import DashboardControls from './components/DashboardControls';
import TemperatureChart from './components/TemperatureChart';
import PrecipitationChart from './components/PrecipitationChart';
import WindChart from './components/WindChart';
import HumidityChart from './components/HumidityChart';
import PressureChart from './components/PressureChart';
import WeatherConditionsChart from './components/WeatherConditionsChart';
import './App.css';

const App: React.FC = () => {
  const [weatherData, setWeatherData] = useState<WeatherData[]>([]);
  const [locations, setLocations] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<DashboardFilters>({
    timeRange: '7d' // Default to show last 7 days of data
  });

  // Helper function to create proper datetime string with hour information in 24h format
  const createDateTimeString = (item: WeatherData): string => {
    const dateStr = item.temps?.date || '';
    const hour = item.temps?.heure || 0;
    const minute = item.temps?.minute || 0;
    
    // Create a proper datetime string in ISO format with 24h time and minutes
    return `${dateStr}T${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}:00`;
  };

  // Fetch locations on component mount
  useEffect(() => {
    const fetchLocations = async () => {
      try {
        const locationsData = await weatherApi.getLocations();
        setLocations(locationsData);
      } catch (err) {
        console.error('Error fetching locations:', err);
        setError('Failed to load locations');
      }
    };

    fetchLocations();
  }, []);

  // Fetch weather data when filters change
  useEffect(() => {
    const fetchWeatherData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const data = await weatherApi.getWeatherData(filters);
        setWeatherData(data);
      } catch (err) {
        console.error('Error fetching weather data:', err);
        setError('Failed to load weather data');
      } finally {
        setLoading(false);
      }
    };

    fetchWeatherData();
  }, [filters]);

  // Transform data for different charts and sort in ascending order (oldest to newest)
  const temperatureData: TemperatureData[] = weatherData
    .map((item: WeatherData) => ({
      date: createDateTimeString(item),
      temperature: item.temperature_celsius,
      location: item.lieu?.nom_ville || 'Unknown'
    }))
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  const precipitationData: PrecipitationData[] = weatherData
    .map((item: WeatherData) => ({
      date: createDateTimeString(item),
      precipitation: item.precipitation_mm,
      location: item.lieu?.nom_ville || 'Unknown'
    }))
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  const windData: WindData[] = weatherData
    .map((item: WeatherData) => ({
      date: createDateTimeString(item),
      windSpeed: item.vent_kph,
      windDirection: item.direction_vent,
      gusts: item.rafales_kph,
      location: item.lieu?.nom_ville || 'Unknown'
    }))
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  const humidityData: HumidityData[] = weatherData
    .map((item: WeatherData) => ({
      date: createDateTimeString(item),
      humidity: item.humidite_pourcentage,
      clouds: item.nuages_pourcentage,
      location: item.lieu?.nom_ville || 'Unknown'
    }))
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  const handleFiltersChange = (newFilters: DashboardFilters) => {
    setFilters(newFilters);
  };

  if (error) {
    return (
      <div className="dashboard-container">
        <div className="dashboard-header">
          <h1>Weather Dashboard</h1>
          <p>Interactive meteorological data visualization</p>
        </div>
        <div className="error">{error}</div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>ECOWAS Weather Dashboard</h1>
        <p>Comprehensive meteorological insights across West African nations</p>
      </div>

      <DashboardControls
        filters={filters}
        onFiltersChange={handleFiltersChange}
        locations={locations}
        loading={loading}
      />

      <div className="chart-grid">
        <TemperatureChart data={temperatureData} loading={loading} />
        <PrecipitationChart data={precipitationData} loading={loading} />
        <WindChart data={windData} loading={loading} />
        <HumidityChart data={humidityData} loading={loading} />
        <PressureChart data={weatherData} loading={loading} />
        <WeatherConditionsChart data={weatherData} loading={loading} />
      </div>
    </div>
  );
};

export default App;

