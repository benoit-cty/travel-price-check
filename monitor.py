"""
Flight monitoring logic for the flight monitor application
"""
import asyncio
import csv
import logging
import subprocess
import time
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QThread
import signal
from config import CHECK_INTERVAL, DEBUG_DIR, PRICE_HISTORY_CSV, CSV_HEADERS, logger, load_travels, LOG_FILE
from gui import LogWindow
from browser import launch_browser, check_single_flight

class AsyncioThread(QThread):
    def __init__(self, coro):
        super().__init__()
        self.coro = coro

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            logger.info("Running async task in separate thread")
            loop.run_until_complete(self.coro)
            logger.info("Async task completed")
        except Exception as e:
            logger.exception(f"Error in AsyncioThread: {e}")
        finally:
            loop.close()

class FlightMonitor(QApplication):
    def __init__(self, sys_args):
        super().__init__(sys_args)
        self.log_window = LogWindow()
        self.setup_logging()
        self.log_window.show()
        self.setup_signal_handling()
        logger.info("Flight Monitor application initialized with GUI")
        self.start_async_check()

    def setup_logging(self):
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        gui_handler = self.log_window.log_widget
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.addHandler(gui_handler)
        logger.setLevel(logging.INFO)

    def setup_signal_handling(self):
        self.orig_sigint_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self.sigint_handler)

    def sigint_handler(self, signum, frame):
        logger.info("SIGINT received, shutting down...")
        self.cleanup()
        self.quit()

    def cleanup(self):
        logger.info("Cleaning up before exit...")
        try:
            logger.info("Disconnecting VPN...")
            subprocess.run(["nordvpn", "disconnect"])
            logger.info("VPN disconnected")
        except Exception as vpn_error:
            logger.error(f"Error disconnecting VPN during cleanup: {vpn_error}")

    def start_async_check(self):
        logger.info("Preparing to start flight checks...")
        self.async_thread = AsyncioThread(self.run_async_check())
        self.async_thread.start()
        logger.info("Async thread started")

    async def run_async_check(self):
        logger.info("Running async flight checks...")
        try:
            while True:
                start_time = time.time()
                logger.info(f"Starting flight price check at {time.strftime('%Y-%m-%d %H:%M:%S')}")
                await self.check_flights()
                logger.info(f"Flight checks completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"Next check scheduled in {CHECK_INTERVAL} seconds ({CHECK_INTERVAL/60:.1f} minutes)")
                elapsed = time.time() - start_time
                wait_time = max(CHECK_INTERVAL - elapsed, 0)
                if wait_time > 0:
                    logger.info(f"Waiting {wait_time:.1f} seconds until next check...")
                    self.log_window.set_next_check_time(time.time() + wait_time)
                    await asyncio.sleep(wait_time)
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt during async operation, cleaning up...")
        except Exception as e:
            logger.exception(f"Error during async check: {e}")

    async def check_flights(self):
        browser = None
        try:
            logger.info("Connecting to VPN...")
            try:
                subprocess.run(["nordvpn", "connect", "BR"], check=True)
                logger.info("VPN connected successfully")
            except Exception as e:
                logger.error(f"VPN connection failed: {e}")
                logger.info("Continuing without VPN...")
            logger.info("Launching browser...")
            browser = await launch_browser()
            page = await asyncio.wait_for(browser.newPage(), timeout=30.0)
            logger.info("Browser page created")
            await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.0 Safari/537.36")
            await page.setViewport({'width': 1200, 'height': 800})
            travels = load_travels()
            logger.info(f"Processing {len(travels)} flights")
            for travel in travels:
                price, price_eur = await check_single_flight(page, travel)
                if price and price_eur:
                    self.save_price_to_csv(travel["flight"], price_eur, price, travel["max_price"])
                await asyncio.sleep(5)
        except Exception as e:
            logger.exception(f"Error during browser automation: {e}")
        finally:
            if browser:
                try:
                    await browser.close()
                    logger.info("Browser closed")
                except Exception as close_error:
                    logger.error(f"Error closing browser: {close_error}")
            try:
                logger.info("Disconnecting VPN...")
                subprocess.run(["nordvpn", "disconnect"], check=True)
                logger.info("VPN disconnected")
            except Exception as vpn_error:
                logger.error(f"Error disconnecting VPN: {vpn_error}")

    def save_price_to_csv(self, flight_info, price_eur, price_brl, max_price):
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            current_time = datetime.now().strftime("%H:%M:%S")
            with open(PRICE_HISTORY_CSV, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([current_date, current_time, flight_info, f"{price_eur:.2f}", f"{price_brl:.2f}", max_price])
            logger.info(f"Saved price for {flight_info} to {PRICE_HISTORY_CSV}")
        except Exception as e:
            logger.error(f"Error saving price to CSV: {e}")

    def show_alert(self, price, max_price, flight_info, price_eur):
        if price < max_price:
            QMessageBox.information(None, "Price Alert", f"Price for {flight_info} dropped to {price:.2f} BRL ({price_eur:.2f} EUR)")
