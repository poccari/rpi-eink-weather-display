"""BOM data 'collector' that downloads the observation data."""
import logging
import requests

#taken from https://github.com/bremor/bureau_of_meteorology
#and modified to work as general library (not async) and removed home assistant references
# by bremor: https://github.com/bremor
"""Constants for PyBoM."""

MAP_MDI_ICON = {
    "clear": "mdi:weather-night",
    "cloudy": "mdi:weather-cloudy",
    "cyclone": "mdi:weather-hurricane",
    "dust": "mdi:weather-hazy",
    "dusty": "mdi:weather-hazy",
    "fog": "mdi:weather-fog",
    "frost": "mdi:snowflake-melt",
    "haze": "mdi:weather-hazy",
    "hazy": "mdi:weather-hazy",
    "heavy_shower": "mdi:weather-pouring",
    "heavy_showers": "mdi:weather-pouring",
    "light_rain": "mdi:weather-partly-rainy",
    "light_shower": "mdi:weather-light-showers",
    "light_showers": "mdi:weather-light-showers",
    "mostly_sunny": "mdi:weather-sunny",
    "partly_cloudy": "mdi:weather-partly-cloudy",
    "rain": "mdi:weather-pouring",
    "shower": "mdi:weather-rainy",
    "showers": "mdi:weather-rainy",
    "snow": "mdi:weather-snowy",
    "storm": "mdi:weather-lightning-rainy",
    "storms": "mdi:weather-lightning-rainy",
    "sunny": "mdi:weather-sunny",
    "tropical_cyclone": "mdi:weather-hurricane",
    "wind": "mdi:weather-windy",
    "windy": "mdi:weather-windy",
    None: None,
}
MAP_UV = {
    "extreme": "Extreme",
    "veryhigh": "Very High",
    "high": "High",
    "moderate": "Moderate",
    "low": "Low",
    None: None,
}

URL_BASE = "https://api.weather.bom.gov.au/v1/locations/"
URL_DAILY = "/forecasts/daily"
URL_HOURLY = "/forecasts/hourly"
URL_OBSERVATIONS = "/observations"
URL_WARNINGS = "/warnings"


def flatten_dict(keys, dict):
    for key in keys:
        if dict[key] is not None:
            flatten = dict.pop(key)
            for inner_key, value in flatten.items():
                dict[key + "_" + inner_key] = value
    return dict

def geohash_encode(latitude, longitude, precision=6):
    base32 = '0123456789bcdefghjkmnpqrstuvwxyz'
    lat_interval = (-90.0, 90.0)
    lon_interval = (-180.0, 180.0)
    geohash = []
    bits = [16, 8, 4, 2, 1]
    bit = 0
    ch = 0
    even = True
    while len(geohash) < precision:
        if even:
            mid = (lon_interval[0] + lon_interval[1]) / 2
            if longitude > mid:
                ch |= bits[bit]
                lon_interval = (mid, lon_interval[1])
            else:
                lon_interval = (lon_interval[0], mid)
        else:
            mid = (lat_interval[0] + lat_interval[1]) / 2
            if latitude > mid:
                ch |= bits[bit]
                lat_interval = (mid, lat_interval[1])
            else:
                lat_interval = (lat_interval[0], mid)
        even = not even
        if bit < 4:
            bit += 1
        else:
            geohash += base32[ch]
            bit = 0
            ch = 0
    return ''.join(geohash)

_LOGGER = logging.getLogger(__name__)

class Collector:
    """Collector for PyBoM."""

    def __init__(self, latitude, longitude):
        """Init collector."""
        self.locations_data = None
        self.observations_data = None
        self.daily_forecasts_data = None
        self.hourly_forecasts_data = None
        self.warnings_data = None
        self.geohash7 = geohash_encode(latitude, longitude)
        self.geohash6 = self.geohash7[:6]

    def get_locations_data(self):
        headers={"User-Agent": "MakeThisAPIOpenSource/1.0.0"}
        """Get JSON location name from BOM API endpoint."""
        
        response = requests.get(URL_BASE + self.geohash7)

        if response is not None and response.status == 200:
            self.locations_data = response.json()

    def format_daily_forecast_data(self):
        """Format forecast data."""
        days = len(self.daily_forecasts_data["data"])
        for day in range(0, days):

            d = self.daily_forecasts_data["data"][day]

            d["mdi_icon"] = MAP_MDI_ICON[d["icon_descriptor"]]

            flatten_dict(["amount"], d["rain"])
            flatten_dict(["rain", "uv", "astronomical"], d)

            if day == 0:
                flatten_dict(["now"], d)

            # If rain amount max is None, set as rain amount min
            if d["rain_amount_max"] is None:
                d["rain_amount_max"] = d["rain_amount_min"]
                d["rain_amount_range"] = d["rain_amount_min"]
            else:
                d["rain_amount_range"] = f"{d['rain_amount_min']}–{d['rain_amount_max']}"

    def format_hourly_forecast_data(self):
        """Format forecast data."""
        hours = len(self.hourly_forecasts_data["data"])
        for hour in range(0, hours):

            d = self.hourly_forecasts_data["data"][hour]

            d["mdi_icon"] = MAP_MDI_ICON[d["icon_descriptor"]]

            flatten_dict(["amount"], d["rain"])
            flatten_dict(["rain", "wind"], d)

            # If rain amount max is None, set as rain amount min
            if d["rain_amount_max"] is None:
                d["rain_amount_max"] = d["rain_amount_min"]
                d["rain_amount_range"] = d["rain_amount_min"]
            else:
                d["rain_amount_range"] = f"{d['rain_amount_min']} to {d['rain_amount_max']}"


    def async_update(self):
        """Refresh the data on the collector object."""
        headers={"User-Agent": "MakeThisAPIOpenSource/1.0.0"}
        response = requests.get(URL_BASE + self.geohash7, headers=headers)
        if response is not None and response.status_code == 200:
            self.locations_data = response.json()
        else:
            _LOGGER.error("Unable to get locations data from BOM API")

        response = requests.get(URL_BASE + self.geohash6 + URL_OBSERVATIONS, headers=headers)
        if response is not None and response.status_code == 200:
            self.observations_data = response.json()
            if self.observations_data["data"].get("wind",None) is not None:
                flatten_dict(["wind"], self.observations_data["data"])
            else:
                self.observations_data["data"]["wind_direction"] = "unavailable"
                self.observations_data["data"]["wind_speed_kilometre"] = "unavailable"
                self.observations_data["data"]["wind_speed_knot"] = "unavailable"
            if self.observations_data["data"]["gust"] is not None:
                flatten_dict(["gust"], self.observations_data["data"])
            else:
                self.observations_data["data"]["gust_speed_kilometre"] = "unavailable"
                self.observations_data["data"]["gust_speed_knot"] = "unavailable"

        resp = requests.get(URL_BASE + self.geohash6 + URL_DAILY, headers=headers)
        if resp is not None and resp.status_code == 200:
            self.daily_forecasts_data = resp.json()
            self.format_daily_forecast_data()

        resp = requests.get(URL_BASE + self.geohash6 + URL_HOURLY, headers=headers)
        if resp is not None and resp.status_code == 200:
            self.hourly_forecasts_data = resp.json()
            self.format_hourly_forecast_data()

        resp = requests.get(URL_BASE + self.geohash6 + URL_WARNINGS, headers=headers)
        if resp is not None and resp.status_code == 200:
            self.warnings_data = resp.json()
            