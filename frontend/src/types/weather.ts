export interface WeatherData {
  id_observation_horaire: number;
  id_dim_lieu_fk: number;
  id_dim_temps_fk: number;
  id_dim_condition_fk: number;
  temperature_celsius: number;
  vent_kph: number;
  vent_degre: number;
  direction_vent: string;
  pression_millibars: number;
  precipitation_mm: number;
  humidite_pourcentage: number;
  nuages_pourcentage: number;
  visibilite_km: number;
  indice_uv: number;
  rafales_kph: number;
  // Joined data from dimension tables
  lieu?: Location;
  temps?: TimeDimension;
  condition?: WeatherCondition;
}

export interface Location {
  id_dim_lieu: number;
  nom_ville: string;
  region?: string;
  pays: string;
}

export interface TimeDimension {
  id_dim_temps: number;
  date: string;
  annee: number;
  mois: number;
  jour: number;
  heure: number;
  minute: number;
  jour_semaine: string;
  nom_mois: string;
}

export interface WeatherCondition {
  id_dim_condition: number;
  code_condition: number;
  texte_condition: string;
}

export interface DashboardFilters {
  location?: string;
  startDate?: string;
  endDate?: string;
  timeRange?: string;
}

export interface ChartDataPoint {
  name: string;
  value: number;
  date?: string;
  location?: string;
}

export interface TemperatureData {
  date: string;
  temperature: number;
  location: string;
}

export interface PrecipitationData {
  date: string;
  precipitation: number;
  location: string;
}

export interface WindData {
  date: string;
  windSpeed: number;
  windDirection: string;
  gusts: number;
  location: string;
}

export interface HumidityData {
  date: string;
  humidity: number;
  clouds: number;
  location: string;
} 