"""
Configuration settings for the flight monitor application
"""
import os
import json
import logging

# Time between price checks (in seconds)
CHECK_INTERVAL = 60 * 60  # 1 hour

# Debug mode flag
DEBUG_MODE = True  # Set to False for production

# Directories and files
DEBUG_DIR = "debug_output"
LOG_FILE = "flight_monitor.log"
PRICE_HISTORY_CSV = "flight_prices.csv"
TRAVELS_JSON = "travels.json"

# Create debug folder
os.makedirs(DEBUG_DIR, exist_ok=True)

# CSV headers for price history
CSV_HEADERS = ["Date", "Time", "Flight", "Price_EUR", "Price_BRL", "Target_Price"]

# Currency conversion rate
BRL_TO_EUR_RATE = 0.160929

# Setup root logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FlightMonitor")

def load_travels():
    """Load travel data from JSON file"""
    try:
        with open(TRAVELS_JSON, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Error loading travels data: {e}")
        # Return empty list as fallback
        return []