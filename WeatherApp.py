import sys
import requests
from io import BytesIO
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QGroupBox, QHBoxLayout
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt

# -----------------------
# Fonts and Styles
# -----------------------
FONT_TITLE = QFont("Segoe UI", 18, QFont.Bold)
FONT_INFO = QFont("Segoe UI", 13)

# -----------------------
# Utility Functions
# -----------------------
def get_location():
    """Get user location via IP"""
    try:
        resp = requests.get("https://ipinfo.io/json", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        loc = data.get("loc", "0,0").split(",")
        city = data.get("city", "Unknown")
        return float(loc[0]), float(loc[1]), city
    except Exception:
        return 0.0, 0.0, "Unknown"

def get_weather(lat, lon):
    """Fetch weather data from Open-Meteo"""
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
            "hourly": "relativehumidity_2m,precipitation,temperature_2m,weathercode,windspeed_10m,winddirection_10m"
        }
        url = "https://api.open-meteo.com/v1/forecast"
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}

def weather_description(code):
    """Map weathercode to description"""
    mapping = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
        55: "Dense drizzle", 56: "Light freezing drizzle", 57: "Dense freezing drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain", 66: "Light freezing rain",
        67: "Heavy freezing rain", 71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
        77: "Snow grains", 80: "Slight rain showers", 81: "Moderate rain showers", 
        82: "Violent rain showers", 85: "Slight snow showers", 86: "Heavy snow showers",
        95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
    }
    return mapping.get(code, f"Code {code}")

def weather_icon_url(code):
    """Map Open-Meteo weather code to OpenWeatherMap icon URL"""
    mapping = {
        0: "01d", 1: "02d", 2: "03d", 3: "04d",
        45: "50d", 48: "50d", 51: "09d", 53: "09d", 55: "09d",
        61: "10d", 63: "10d", 65: "10d", 66: "10d", 67: "10d",
        71: "13d", 73: "13d", 75: "13d",
        77: "13d", 80: "09d", 81: "09d", 82: "09d",
        95: "11d", 96: "11d", 99: "11d"
    }
    icon_code = mapping.get(code, "01d")
    return f"http://openweathermap.org/img/wn/{icon_code}@2x.png"

def load_icon_from_url(url, size=100):
    """Load QPixmap from URL"""
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        img_data = resp.content
        pixmap = QPixmap()
        pixmap.loadFromData(img_data)
        pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return pixmap
    except Exception:
        return QPixmap(size, size)  # blank placeholder

# -----------------------
# Main App
# -----------------------
class WeatherApp(QWidget):
    def __init__(self, city, weather_json):
        super().__init__()
        self.setWindowTitle("Weather Dashboard")
        self.setStyleSheet("background-color: #1e1e2f; color: #ffffff;")

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        # City label
        city_label = QLabel(f"Weather in {city}")
        city_label.setFont(FONT_TITLE)
        city_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(city_label)

        # Extract weather data safely
        current = weather_json.get("current_weather", {})
        hourly = weather_json.get("hourly", {})
        idx = 0  # use first hourly data point

        humidity = hourly.get("relativehumidity_2m", [])
        precipitation = hourly.get("precipitation", [])
        temps = hourly.get("temperature_2m", [])
        weathercodes = hourly.get("weathercode", [])
        wind_speeds = hourly.get("windspeed_10m", [])
        wind_dirs = hourly.get("winddirection_10m", [])

        # Build panel
        panel = QGroupBox()
        panel.setStyleSheet("""
            QGroupBox {
                background-color: #2c2c44;
                border-radius: 12px;
                margin: 10px;
                padding: 12px;
            }
        """)
        panel_layout = QHBoxLayout()

        # Icon
        code = int(current.get("weathercode", 0))
        icon_pix = load_icon_from_url(weather_icon_url(code))
        icon_label = QLabel()
        icon_label.setPixmap(icon_pix)
        panel_layout.addWidget(icon_label)

        # Info labels
        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignTop)

        labels = {
            "Temperature": f"{current.get('temperature', 'N/A')} °C",
            "Condition": weather_description(code),
            "Wind": f"{current.get('windspeed', 'N/A')} km/h, {current.get('winddirection', 'N/A')}°",
            "Humidity": f"{humidity[idx] if idx < len(humidity) else 'N/A'} %",
            "Precipitation": f"{precipitation[idx] if idx < len(precipitation) else 'N/A'} mm",
            "Forecast Temp": f"{temps[idx] if idx < len(temps) else 'N/A'} °C",
            "Forecast Wind": f"{wind_speeds[idx] if idx < len(wind_speeds) else 'N/A'} km/h, {wind_dirs[idx] if idx < len(wind_dirs) else 'N/A'}°",
            "Forecast Condition": weather_description(weathercodes[idx]) if idx < len(weathercodes) else "N/A"
        }

        for k, v in labels.items():
            lbl = QLabel(f"{k}: {v}")
            lbl.setFont(FONT_INFO)
            info_layout.addWidget(lbl)

        panel_layout.addLayout(info_layout)
        panel.setLayout(panel_layout)
        layout.addWidget(panel)

        self.setLayout(layout)
        self.adjustSize()  # Let the window resize to fit all content
        self.setMinimumWidth(500)  # Optional: keep a reasonable width

# -----------------------
# Run App
# -----------------------
if __name__ == "__main__":
    lat, lon, city = get_location()
    weather_json = get_weather(lat, lon)

    app = QApplication(sys.argv)
    window = WeatherApp(city, weather_json)
    window.show()
    sys.exit(app.exec_())
