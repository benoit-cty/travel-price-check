"""
uv run booking.py
ps -ef | grep book

curl 'https://booking.flytap.com/bfm/rest/booking/availability/searchMulti/' --compressed -X POST -H 'User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0' -H 'Accept: application/json, text/plain, */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br, zstd' -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiItYnFCaW5CaUh6NFlnKzg3Qk4rUFUzVGFYVVd5UnJuMVQvaVYvTGp4Z2VTQT0iLCJzY29wZXMiOlsiUk9MRV9BTk9OWU1PVVNfVVNFUiJdLCJob3N0IjoidHBwcm8td2ZpYmUtdm1zczAwMDA2MC5pbnRlcm5hbC5jbG91ZGFwcC5uZXQiLCJyYW5kb20iOiJWNzg4ViIsImlhdCI6MTc0Mjg1MDgwMCwiZXhwIjoxNzQyODY4ODAwfQ.1JKHPOnPwH4Ah86jK-F8O9Nqo1uQ6iwGFgBhqTrf8QQ' -H 'Content-Type: application/json' -H 'Origin: https://booking.flytap.com' -H 'DNT: 1' -H 'Sec-GPC: 1' -H 'Connection: keep-alive' -H 'Referer: https://booking.flytap.com/booking/flights-stopover' -H 'Cookie: httpECXCORS=4f0cf7985f6b350d03537b73c33ea7fe; httpECX=4f0cf7985f6b350d03537b73c33ea7fe; __cf_bm=CqHKDQIYK0Jg2zaDT3grgZCDE.D2nDWIDZj4YmSDmsg-1742850798-1.0.1.1-dm63QLnpsA.yN9of_t.RbPWRnpTfIQW33z2.4Z4x85ZMXs4V9r7NAgUdfFZnL4jXXQXrCyYNZ6PGlum.PubMhHfZyxA_iSHuIwK1UXDwmsk; OptanonConsent=isGpcEnabled=1&datestamp=Mon+Mar+24+2025+22%3A13%3A20+GMT%2B0100+(Central+European+Standard+Time)&version=202502.1.0&browserGpcFlag=1&isIABGlobal=false&hosts=&genVendors=V2%3A0%2CV1%3A0%2C&consentId=524d8f0b-c279-48f4-a5ae-4873c42e68c6&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1&intType=1&geolocation=%3B&AwaitingReconsent=false; OptanonAlertBoxClosed=2025-03-24T21:04:52.194Z; _gcl_au=1.1.770081092.1742850292' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: same-origin' -H 'Priority: u=0' -H 'TE: trailers' --data-raw '{"adt":4,"airlineId":"TP","bfmModule":"BFM_BOOKING","c14":0,"cabinClass":"E","changeReturn":false,"channelDetectionName":"","chd":0,"cmsId":"string","communities":[],"departureDate":["20072025","22072025","10082025"],"destination":["LIS","GIG","ORY"],"groups":[],"inf":0,"language":"en","market":"PT","multiCityTripType":false,"numSeat":4,"numSeats":4,"oneWay":true,"origin":["ORY","LIS","SSA"],"passengers":{"ADT":4,"YTH":0,"CHD":0,"INF":0},"paxSearch":{"ADT":4,"YTH":0,"CHD":0,"INF":0},"permittedCabins":[],"preferredCarrier":[],"promocode":"","promotionId":"","returnDate":"","roundTripType":false,"searchPoint":true,"session":"string","tripType":"M","validTripType":true,"yth":0,"stopOverOutboundLocation":"LIS","stopOverMulticityLocation":["ORY","GIG"]}'

"""
import asyncio
import sys
import time
import subprocess
import re
import os
import logging
import shutil
import threading
from datetime import datetime
from pyppeteer import launch
from PyQt5.QtWidgets import QApplication, QMessageBox, QMainWindow, QTextEdit, QVBoxLayout, QPushButton, QWidget
from PyQt5.QtCore import QObject, pyqtSignal, Qt, QTimer, QThread
import signal

# Setup root logger without handlers initially
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get the logger
logger = logging.getLogger("FlightMonitor")

# Custom QT handler for logging
class QTextEditLogger(logging.Handler, QObject):
    log_signal = pyqtSignal(str)
    
    def __init__(self, parent=None):
        logging.Handler.__init__(self)
        QObject.__init__(self, parent)
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.log_signal.connect(self.log_output)
        self.widget = QTextEdit()
        self.widget.setReadOnly(True)
    
    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(msg)
    
    def log_output(self, msg):
        cursor = self.widget.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(msg + '\n')
        self.widget.setTextCursor(cursor)
        self.widget.ensureCursorVisible()

# LogWindow class to display logs in a QT window
class LogWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Flight Monitor Logs")
        self.setGeometry(100, 100, 800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        
        # Log widget
        self.log_widget = QTextEditLogger(self)
        layout.addWidget(self.log_widget.widget)
        
        # Stop button
        self.stop_button = QPushButton("Stop Monitor")
        self.stop_button.clicked.connect(self.stop_monitor)
        layout.addWidget(self.stop_button)
    
    def stop_monitor(self):
        logger.info("Stop button clicked, shutting down...")
        app = QApplication.instance()
        if app and hasattr(app, 'cleanup'):
            app.cleanup()
            app.quit()

# Custom thread for running asyncio event loop
class AsyncioThread(QThread):
    def __init__(self, coro):
        super().__init__()
        self.coro = coro
    
    def run(self):
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the coroutine
            logger.info("Running async task in separate thread")
            loop.run_until_complete(self.coro)
            logger.info("Async task completed")
        except Exception as e:
            logger.exception(f"Error in AsyncioThread: {e}")
        finally:
            # Clean up the loop
            loop.close()

# travels
travels = [
    {
        # Vol Rio de Janeiro -> Brasilia
        "flight":"SDU->BSB",
        "url":"https://flights.booking.com/flights/SDU.AIRPORT-BSB.AIRPORT/?type=ONEWAY&adults=2&cabinClass=ECONOMY&children=12%2C12&from=SDU.AIRPORT&to=BSB.AIRPORT&fromCountry=BR&toCountry=BR&fromLocationName=Santos+Dumont+Airport&toLocationName=Brasilia+-+Presidente+Juscelino+Kubitschek+International+Airport&stops=0&depart=2025-07-26&sort=BEST&travelPurpose=leisure&ca_source=flights_search_sb",
        "max_price": 1_500,
    },
    {
        "flight":"BSB->SSA",
        "url":"https://flights.booking.com/flights/BSB.AIRPORT-SSA.AIRPORT/?type=ONEWAY&adults=2&cabinClass=ECONOMY&children=12%2C12&from=BSB.AIRPORT&to=SSA.AIRPORT&fromCountry=BR&toCountry=BR&fromLocationName=Brasilia+-+Presidente+Juscelino+Kubitschek+International+Airport&toLocationName=Salvador+International+Airport&depart=2025-08-04&sort=BEST&travelPurpose=leisure&ca_source=flights_index_sb",
        "max_price": 1_700,
    },
    {
        "flight":"ORY->GIG, SSA->ORY",
        "url": "https://flights.booking.com/flights/ORY.AIRPORT|SSA.AIRPORT-GIG.AIRPORT|ORY.AIRPORT/?type=MULTISTOP&adults=2&cabinClass=ECONOMY&children=12%2C12&from=ORY.AIRPORT%7CSSA.AIRPORT&to=GIG.AIRPORT%7CORY.AIRPORT&fromCountry=FR%7CBR&toCountry=BR%7CFR&fromLocationName=Paris+-+Orly+Airport%7CSalvador+International+Airport&toLocationName=Rio+de+Janeiro%2FGaleao+International+Airport%7CParis+-+Orly+Airport&stops=1&multiStopDates=2025-07-21%7C2025-08-10&sort=BEST&travelPurpose=leisure&ca_source=flights_search_sb",
        "max_price": 27_000,
    }
]

CHECK_INTERVAL = 60*60  # in seconds
DEBUG_MODE = True  # Set to False for production

# Create debug folder
debug_dir = "debug_output"
os.makedirs(debug_dir, exist_ok=True)

class FlightMonitor(QApplication):
    def __init__(self, sys_args):
        super().__init__(sys_args)
        
        # Create and show log window
        self.log_window = LogWindow()
        
        # Set up the logging configuration
        self.setup_logging()
        
        # Show the window after setting up logging
        self.log_window.show()
        
        # Set up signal handling directly in the class
        self.setup_signal_handling()
        
        # Initial log message to verify logging works
        logger.info("Flight Monitor application initialized with GUI")
        
        # Start the flight checking asynchronously
        self.start_async_check()
    
    def setup_logging(self):
        """Set up logging with handlers for file, console, and GUI"""
        # Remove all existing handlers to avoid duplicates
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create file handler
        file_handler = logging.FileHandler("flight_monitor.log")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # Add GUI handler
        gui_handler = self.log_window.log_widget
        
        # Add all handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.addHandler(gui_handler)
        
        # Set level for the logger itself
        logger.setLevel(logging.INFO)
        
    def setup_signal_handling(self):
        # Create a socket pair for SIGINT handling
        self.orig_sigint_handler = signal.getsignal(signal.SIGINT)
        
        # Install signal handler
        signal.signal(signal.SIGINT, self.sigint_handler)
        
    def sigint_handler(self, signum, frame):
        # Log the signal reception
        logger.info("SIGINT received, shutting down...")
        # Clean up and quit
        self.cleanup()
        self.quit()
        
    def cleanup(self):
        """Perform cleanup operations before exiting"""
        logger.info("Cleaning up before exit...")
        # Disconnect VPN if needed
        try:
            logger.info("Disconnecting VPN...")
            subprocess.run(["nordvpn", "disconnect"])
            logger.info("VPN disconnected")
        except Exception as vpn_error:
            logger.error(f"Error disconnecting VPN during cleanup: {vpn_error}")

    def start_async_check(self):
        """Start the async check in a separate thread"""
        logger.info("Preparing to start flight checks...")
        
        # Create and start a thread for running the asyncio event loop
        self.async_thread = AsyncioThread(self.run_async_check())
        self.async_thread.start()
        logger.info("Async thread started")

    async def run_async_check(self):
        """Run the flight checks"""
        logger.info("Running async flight checks...")
        try:
            await self.check_flights()
            logger.info("Flight checks completed")
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt during async operation, cleaning up...")
        except Exception as e:
            logger.exception(f"Error during async check: {e}")

    async def check_flights(self):
        """Check prices for all flights in the travels list"""
        browser = None
        try:
            # Connect to VPN
            logger.info("Connecting to VPN...")
            try:
                subprocess.run(["nordvpn", "connect", "BR"], check=True)
                logger.info("VPN connected successfully")
            except Exception as e:
                logger.error(f"VPN connection failed: {e}")
                logger.info("Continuing without VPN...")
            
            # Use the same configuration that worked in the diagnostic test
            logger.info("Launching browser...")
            browser = await launch(
                headless=True,  # Keep headless since it worked in the test
                handleSIGINT=False,  # Disable SIGINT handling to avoid thread issues
                handleSIGTERM=False,  # Disable SIGTERM handling to avoid thread issues
                handleSIGHUP=False,  # Disable SIGHUP handling to avoid thread issues
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )
            logger.info("Browser launched successfully!")
            
            # Create a new page with timeout handling
            page = await asyncio.wait_for(
                browser.newPage(),
                timeout=30.0
            )
            logger.info("Browser page created")
            
            # Set realistic browser headers
            await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.0 Safari/537.36")
            
            # Set viewport size
            await page.setViewport({'width': 1200, 'height': 800})
            
            # Process each flight in the travels list
            logger.info(f"Processing {len(travels)} flights")
            for travel in travels:
                await self.check_single_flight(page, travel)
                # Add a small delay between flight checks to avoid overloading
                await asyncio.sleep(5)
                
        except Exception as e:
            logger.exception(f"Error during browser automation: {e}")
            
        finally:
            # Close browser if it was successfully created
            if browser:
                try:
                    await browser.close()
                    logger.info("Browser closed")
                except Exception as close_error:
                    logger.error(f"Error closing browser: {close_error}")
                
            # Disconnect VPN
            try:
                logger.info("Disconnecting VPN...")
                subprocess.run(["nordvpn", "disconnect"], check=True)
                logger.info("VPN disconnected")
            except Exception as vpn_error:
                logger.error(f"Error disconnecting VPN: {vpn_error}")

    async def check_single_flight(self, page, travel):
        """Check a single flight from the travel list"""
        flight_info = travel["flight"]
        url = travel["url"] 
        max_price = travel["max_price"]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        flight_debug_id = f"{flight_info.replace(' ', '_').replace(',', '')}_{timestamp}"
        
        logger.info(f"Checking flight: {flight_info} with max price: {max_price}")
        
        try:
            # Navigate to page with longer timeout
            logger.info(f"Navigating to URL for flight {flight_info}")
            response = await asyncio.wait_for(
                page.goto(url, {'waitUntil': 'networkidle2'}),
                timeout=120.0  # Longer timeout for page navigation
            )
            
            if not response:
                logger.error(f"Failed to get response from page navigation for flight {flight_info}")
                await page.screenshot({'path': f'{debug_dir}/navigation_error_{flight_debug_id}.png'})
                return
                
            logger.info(f"Page loaded with status: {response.status}")
            
            # Take screenshot after initial page load
            logger.info(f"Taking initial screenshot for flight {flight_info}...")
            await page.waitForFunction('document.body !== null && document.body.clientWidth > 0')  # Wait until page has a non-zero width
            time.sleep(2)  # Additional wait to ensure page is fully loaded
            await page.screenshot({'path': f'{debug_dir}/initial_load_{flight_debug_id}.png', 'fullPage': True})
            
            # Save HTML content
            html_content = await page.content()
            with open(f'{debug_dir}/page_content_{flight_debug_id}.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML content saved to {debug_dir}/page_content_{flight_debug_id}.html")
            
            # Wait for price element with more detailed error handling
            try:
                logger.info(f"Waiting for price element for flight {flight_info}...")
                # Updated selector based on your example
                price_selectors = [
                    'span.Text-module__root--color-neutral_alt___SfoVN',
                    '[data-testid="search_filter_stops_radio_Direct only"] span:contains("€")',
                    'div[data-testid="search_filter_stops_radio_Direct only"]',
                    'span[class*="neutral_alt"]',
                    'div.bui-price-display__value'  # Additional selector for different formats
                ]
                
                found_price_element = False
                for selector in price_selectors:
                    try:
                        logger.info(f"Trying selector: {selector}")
                        await asyncio.wait_for(
                            page.waitForSelector(selector),
                            timeout=10.0
                        )
                        logger.info(f"Found price element with selector: {selector} for flight {flight_info}")
                        found_price_element = True
                        break
                    except Exception:
                        continue
                
                if not found_price_element:
                    logger.warning(f"None of the price selectors found an element for flight {flight_info}")
                    # Try JavaScript evaluation as a fallback
                    logger.info("Attempting JavaScript price extraction...")
                    
                await page.screenshot({'path': f'{debug_dir}/price_found_{flight_debug_id}.png', 'fullPage': True})
                
                # Get page content for price
                content = await page.content()
                
                # JavaScript evaluation for price extraction
                prices = await page.evaluate('''
                    () => {
                        // Try multiple selectors to find prices
                        const priceElements = [
                            ...document.querySelectorAll('span.Text-module__root--color-neutral_alt___SfoVN'),
                            ...document.querySelectorAll('div.bui-price-display__value'),
                            ...document.querySelectorAll('[data-testid="flight-card-price"]'),
                            ...document.querySelectorAll('span[class*="neutral_alt"]')
                        ];
                        
                        const prices = [];
                        priceElements.forEach(el => {
                            const text = el.textContent.trim();
                            if (text.includes('BRL') || text.includes('€') || text.includes('R$')) {
                                prices.push(text);
                            }
                        });
                        
                        return prices;
                    }
                ''')
                
                logger.info(f"JavaScript found prices: {prices}")
                
                # Try multiple approaches to find the price
                price = None
                
                # Method 1: JavaScript price extraction
                if prices and len(prices) > 0:
                    for price_text in prices:
                        # Match price patterns (BRL, €, R$)
                        price_match = re.search(r"(?:BRL|€|R\$)[\s]*([\d,.]+)", price_text)
                        if price_match:
                            try:
                                # Improved price parsing for international formats
                                price_str = price_match.group(1)
                                
                                # Determine the format: 1,234.56 (US/UK) or 1.234,56 (EU)
                                if ',' in price_str and '.' in price_str:
                                    # Format with both comma and period (e.g. 1,234.56)
                                    if price_str.find(',') < price_str.find('.'):
                                        # US/UK format: 1,234.56 -> remove commas
                                        price_str = price_str.replace(',', '')
                                    else:
                                        # EU format: 1.234,56 -> convert to US format
                                        price_str = price_str.replace('.', '').replace(',', '.')
                                elif ',' in price_str:
                                    # Only comma present - could be decimal or thousand separator
                                    # For Booking.com, we assume it's a decimal separator if it's near the end
                                    if len(price_str) - price_str.rfind(',') <= 3:
                                        # Decimal separator: 1234,56 -> 1234.56
                                        price_str = price_str.replace(',', '.')
                                    else:
                                        # Thousand separator: 1,234 -> 1234
                                        price_str = price_str.replace(',', '')
                                
                                # Convert to float
                                price_val = float(price_str)
                                
                                if price is None or price_val < price:
                                    price = price_val
                                    logger.info(f"Parsed price {price_text} as {price_val}")
                            except ValueError as ve:
                                logger.error(f"Error parsing price {price_text}: {ve}")
                                continue
                
                # Method 2: Regular expression on HTML content
                if not price:
                    # Search for price patterns in the HTML content
                    price_patterns = [
                        r"From BRL[\s]*([\d.,]+)",
                        r"From €[\s]*([\d.,]+)",
                        # r"R\$[\s]*([\d.,]+)",
                        # r"BRL[\s]*([\d.,]+)",
                        # r"€[\s]*([\d.,]+)"
                    ]
                    
                    for pattern in price_patterns:
                        price_match = re.search(pattern, content)
                        if price_match:
                            try:
                                price_str = price_match.group(1).replace(".", "").replace(",", ".")
                                price_val = float(price_str)
                                if price is None or price_val < price:
                                    price = price_val
                            except ValueError:
                                continue
                
                if price:
                    logger.info(f"Found price for {flight_info}: {price:.2f}")
                    if price < max_price:
                        self.show_alert(price, max_price, flight_info)
                    else:
                        logger.info(f"Price for {flight_info} is above target: {price:.2f} (Target: {max_price})")
                else:
                    logger.error(f"Price not found for flight {flight_info}")
                    
            except Exception as e:
                logger.error(f"Error finding price element for flight {flight_info}: {e}")
                
                # Take error screenshot with non-zero width check
                await page.waitForFunction('document.body !== null && document.body.clientWidth > 0')
                await page.screenshot({'path': f'{debug_dir}/error_{flight_debug_id}.png', 'fullPage': True})
                
                # Save HTML for debugging
                html_content = await page.content()
                with open(f'{debug_dir}/page_error_{flight_debug_id}.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.info(f"HTML content saved to {debug_dir}/page_error_{flight_debug_id}.html")
                
        except Exception as e:
            logger.exception(f"Error checking flight {flight_info}: {e}")

    def show_alert(self, price, max_price, flight_info):
        """Show alert dialog for price drops"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(f"Price Alert for {flight_info}!")
        
        # Format large numbers with thousands separator for better readability
        formatted_price = f"{price:,.2f}".replace(",", " ")
        formatted_max_price = f"{max_price:,.2f}".replace(",", " ")
        
        msg.setText(f"Flight {flight_info} price dropped to BRL {formatted_price}!\n(Threshold: BRL {formatted_max_price})")
        msg.exec_()

if __name__ == "__main__":
    logger.info("Starting Flight Monitor application")
    try:
        app = FlightMonitor(sys.argv)
        print("Flight Monitor application started")
        signal.signal(signal.SIGINT, lambda s, f: app.quit())  # Enable Ctrl+C to gracefully quit
        sys.exit(app.exec_())
    except Exception as e:
        logger.exception(f"Error starting Flight Monitor application: {e}")
        sys.exit(1)