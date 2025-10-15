import os
import requests
from typing import Optional, Tuple, List, Dict, Union
from strands import Agent, tool

BASE_OPENWEATHER_URL = "http://api.openweathermap.org"


def geocode(city: str, country: str, state: Optional[str] = None) -> Tuple[float, float]:
    """Helper function to convert a location into its latitute and longitude"""
    state = state + ',' if state else ''
    url = f"{BASE_OPENWEATHER_URL}/geo/1.0/direct?q={city},{state}{country}&appid={os.getenv('OPENWEATHER_API_KEY')}"
    r = requests.get(url).json()
    return r[0]['lat'], r[0]['lon']


@tool
def get_aqi(city: str, country: str, state: Optional[str] = None) -> Tuple[str, float]:
    """Get air quality index for a given location.

    Args:
        city: city name of the location
        country: country of the location
        state: (optional) state of the location, if in US
    """
    lat, long = geocode(city, country, state)
    url = f"{BASE_OPENWEATHER_URL}/data/2.5/air_pollution?lat={lat}&lon={long}&appid={os.getenv('OPENWEATHER_API_KEY')}"
    response = requests.get(url).json()
    index_mapping = {
        1: "Good",
        2: "Fair",
        3: "Moderate",
        4: "Poor",
        5: "Very Poor"
    }
    air_pollution = response['list'][0]
    aqi = air_pollution['main']['aqi']
    pm2_5 = air_pollution['components']['pm2_5']
    return index_mapping[aqi], pm2_5


@tool
def get_current_weather(city: str, country: str, state: Optional[str] = None) -> Dict[str, Union[float, int, List[str]]]:
    """Get weather information for a given location.

    Args:
        city: city name of the location
        country: country of the location
        state: (optional) state of the location, if in US
    Returns:
        dict: (temperature: float, humidity: int, uv_index: int, alerts: list[str])
    """
    lat, long = geocode(city, country, state)
    url = f"{BASE_OPENWEATHER_URL}/data/3.0/onecall?lat={lat}&lon={long}&appid={os.getenv('OPENWEATHER_API_KEY')}"
    response = requests.get(url).json()

    alerts = [alert['description'] for alert in response['alerts']] if 'alerts' in response else []
    return {
        'temperature': response['current']['temp'],
        'humidity': response['current']['humidity'], 
        'uv_index': response['current']['uvi'], 
        'alerts': alerts
    }
