#!/usr/bin/env python3
"""
Simple test script to verify the Flask API endpoints work correctly.
Run this after starting the Flask backend to test the API.
"""

import requests
import json
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://127.0.0.1:25451"

def test_locations_endpoint():
    """Test the locations endpoint"""
    print("Testing /api/weather/locations...")
    try:
        response = requests.get(f"{BASE_URL}/api/weather/locations")
        if response.status_code == 200:
            locations = response.json()
            print(f"✅ Success! Found {len(locations)} locations")
            print(f"Sample locations: {locations}")
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_weather_data_endpoint():
    """Test the weather data endpoint with different filters"""
    print("\nTesting /api/weather/data...")
    
    # Test 1: No filters (should return all data)
    print("Test 1: No filters")
    try:
        response = requests.get(f"{BASE_URL}/api/weather/data")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data)} weather records")
            if data:
                print(f"Sample record: {json.dumps(data[0], indent=2)}")
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_weather_data_with_filters():
    """Test the weather data endpoint with filters"""
    print("\nTest 2: With time range filter (7d)")
    try:
        response = requests.get(f"{BASE_URL}/api/weather/data?timeRange=7d")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data)} weather records for last 7 days")
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_weather_data_with_location():
    """Test the weather data endpoint with location filter"""
    print("\nTest 3: With location filter")
    try:
        # First get locations to use a valid one
        locations_response = requests.get(f"{BASE_URL}/api/weather/locations")
        if locations_response.status_code == 200:
            locations = locations_response.json()
            if locations:
                test_location = locations[0]
                response = requests.get(f"{BASE_URL}/api/weather/data?location={test_location}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Success! Found {len(data)} weather records for {test_location}")
                    return True
                else:
                    print(f"❌ Error: {response.status_code} - {response.text}")
                    return False
            else:
                print("❌ No locations available for testing")
                return False
        else:
            print(f"❌ Error getting locations: {locations_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting API tests...")
    print("=" * 50)
    
    # Test locations endpoint
    locations_ok = test_locations_endpoint()
    
    # Test weather data endpoint
    weather_ok = test_weather_data_endpoint()
    
    # Test with filters
    filters_ok = test_weather_data_with_filters()
    
    # Test with location
    location_ok = test_weather_data_with_location()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"Locations endpoint: {'✅ PASS' if locations_ok else '❌ FAIL'}")
    print(f"Weather data (no filters): {'✅ PASS' if weather_ok else '❌ FAIL'}")
    print(f"Weather data (with time filter): {'✅ PASS' if filters_ok else '❌ FAIL'}")
    print(f"Weather data (with location filter): {'✅ PASS' if location_ok else '❌ FAIL'}")
    
    if all([locations_ok, weather_ok, filters_ok, location_ok]):
        print("\n🎉 All tests passed! The API is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the Flask backend and database connection.")

if __name__ == "__main__":
    main() 