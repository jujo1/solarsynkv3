"""Configuration constants for SolarSynkV3."""

# API Configuration
DEFAULT_TIMEOUT = 10
SUNSYNK_API_BASE_URL = "https://api.sunsynk.net"
PUBLIC_KEY_ENDPOINT = "/anonymous/publicKey"
TOKEN_ENDPOINT = "/oauth/token/new"

# File paths
DEFAULT_SETTINGS_PATH = '/data/options.json'
LOG_FILE_PATH = "solar_script.log"
SETTINGS_FILE = "settings.json"
SERVER_SETTINGS_FILE = "svr_settings.json"

# Authentication
CLIENT_ID = "csp-web"
GRANT_TYPE = "password"
AREA_CODE = "sunsynk"
SOURCE = "sunsynk"

# Home Assistant
HA_SENSOR_PREFIX = "sensor.solarsynkv3_"
CONNECTION_TEST_VALUES = {
    "serial": "TEST",
    "uom": "A",
    "uom_long": "current",
    "friendly_name": "connection_test",
    "short_name": "connection_test_current",
    "value": "100"
}

# Units of measurement
ENERGY_UNIT = "kWh"
POWER_UNIT = "W"
VOLTAGE_UNIT = "V"
CURRENT_UNIT = "A"
TEMPERATURE_UNIT = "°C"

# State classes
STATE_CLASS_MEASUREMENT = "measurement"
STATE_CLASS_TOTAL_INCREASING = "total_increasing"

# Device classes
DEVICE_CLASS_ENERGY = "energy"
DEVICE_CLASS_POWER = "power"
DEVICE_CLASS_VOLTAGE = "voltage"
DEVICE_CLASS_CURRENT = "current"
DEVICE_CLASS_TEMPERATURE = "temperature"
