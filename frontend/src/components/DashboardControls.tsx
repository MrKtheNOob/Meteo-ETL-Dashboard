import React from 'react';
import { DashboardFilters } from '../types/weather';

interface DashboardControlsProps {
  filters: DashboardFilters;
  onFiltersChange: (filters: DashboardFilters) => void;
  locations: string[];
  loading?: boolean;
}

const DashboardControls: React.FC<DashboardControlsProps> = ({
  filters,
  onFiltersChange,
  locations,
  loading = false
}) => {
  const handleLocationChange = (location: string) => {
    // If "All Locations" is selected (empty string value), set location to undefined
    onFiltersChange({ ...filters, location: location === '' ? undefined : location });
  };

  const handleStartDateChange = (startDate: string) => {
    onFiltersChange({ ...filters, startDate });
  };

  const handleEndDateChange = (endDate: string) => {
    onFiltersChange({ ...filters, endDate });
  };

  const handleTimeRangeChange = (timeRange: string) => {
    onFiltersChange({ ...filters, timeRange });
  };

  const getDefaultDates = () => {
    const today = new Date();
    const lastWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
    
    return {
      startDate: lastWeek.toISOString().split('T')[0],
      endDate: today.toISOString().split('T')[0]
    };
  };

  // We don't use these directly for input values as filters take precedence,
  // but they can be used for initial filter state if filters are empty.
  getDefaultDates();

  return (
    <div className="controls-section">
      <div className="controls-grid">
        <div className="control-group">
          <label htmlFor="location">Location</label>
          <select
            id="location"
            // Ensure the value is an empty string when no location is selected to correctly display "All Locations"
            value={filters.location || ''}
            onChange={(e) => handleLocationChange(e.target.value)}
            disabled={loading}
          >
            {/* Option for "All Locations" */}
            <option value="">All Locations</option>
            {locations.map((location) => (
              <option key={location} value={location}>
                {location}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="startDate">Start Date</label>
          <input
            type="date"
            id="startDate"
            value={filters.startDate || ''} // Use empty string for controlled component
            onChange={(e) => handleStartDateChange(e.target.value)}
            disabled={loading}
          />
        </div>

        <div className="control-group">
          <label htmlFor="endDate">End Date</label>
          <input
            type="date"
            id="endDate"
            value={filters.endDate || ''} // Use empty string for controlled component
            onChange={(e) => handleEndDateChange(e.target.value)}
            disabled={loading}
          />
        </div>

        <div className="control-group">
          <label htmlFor="timeRange">Time Range</label>
          <select
            id="timeRange"
            value={filters.timeRange || ''}
            onChange={(e) => handleTimeRangeChange(e.target.value)}
            disabled={loading}
          >
            <option value="">Custom Range</option>
            <option value="1d">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
        </div>
      </div>
    </div>
  );
};

export default DashboardControls;
