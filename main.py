"""
Entry point for the flight monitor application
"""
import sys
import signal
from monitor import FlightMonitor
from config import logger

if __name__ == "__main__":
    logger.info("Starting Flight Monitor application")
    try:
        app = FlightMonitor(sys.argv)
        signal.signal(signal.SIGINT, lambda s, f: app.quit())  # Enable Ctrl+C to gracefully quit
        sys.exit(app.exec_())
    except Exception as e:
        logger.exception(f"Error starting Flight Monitor application: {e}")
        sys.exit(1)