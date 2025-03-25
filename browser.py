"""
Browser automation tasks for the flight monitor application
"""
import asyncio
from pyppeteer import launch
import logging
from datetime import datetime
import time
import re
from config import DEBUG_DIR, BRL_TO_EUR_RATE, logger

async def launch_browser():
    """Launch the browser and return the browser instance"""
    logger.info("Launching browser...")
    browser = await launch(
        headless=True,
        handleSIGINT=False,
        handleSIGTERM=False,
        handleSIGHUP=False,
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu'
        ]
    )
    logger.info("Browser launched successfully!")
    return browser

async def check_single_flight(page, travel):
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
            await page.screenshot({'path': f'{DEBUG_DIR}/navigation_error_{flight_debug_id}.png'})
            return

        logger.info(f"Page loaded with status: {response.status}")

        # Take screenshot after initial page load
        logger.info(f"Taking initial screenshot for flight {flight_info}...")
        await page.waitForFunction('document.body !== null && document.body.clientWidth > 0')  # Wait until page has a non-zero width
        time.sleep(2)  # Additional wait to ensure page is fully loaded
        await page.screenshot({'path': f'{DEBUG_DIR}/initial_load_{flight_debug_id}.png', 'fullPage': True})

        # Save HTML content
        html_content = await page.content()
        with open(f'{DEBUG_DIR}/page_content_{flight_debug_id}.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"HTML content saved to {DEBUG_DIR}/page_content_{flight_debug_id}.html")

        # Wait for price element with more detailed error handling
        try:
            logger.info(f"Waiting for price element for flight {flight_info}...")
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
                logger.info("Attempting JavaScript price extraction...")

            await page.screenshot({'path': f'{DEBUG_DIR}/price_found_{flight_debug_id}.png', 'fullPage': True})

            # Get page content for price
            content = await page.content()

            # JavaScript evaluation for price extraction
            prices = await page.evaluate('''
                () => {
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

            price = None

            if prices and len(prices) > 0:
                for price_text in prices:
                    price_match = re.search(r"(?:BRL|€|R\$)[\s]*([\d,.]+)", price_text)
                    if price_match:
                        try:
                            price_str = price_match.group(1)
                            if ',' in price_str and '.' in price_str:
                                if price_str.find(',') < price_str.find('.'):  # US/UK format
                                    price_str = price_str.replace(',', '')
                                else:  # EU format
                                    price_str = price_str.replace('.', '').replace(',', '.')
                            elif ',' in price_str:
                                if len(price_str) - price_str.rfind(',') <= 3:
                                    price_str = price_str.replace(',', '.')
                                else:
                                    price_str = price_str.replace(',', '')

                            price_val = float(price_str)

                            if price is None or price_val < price:
                                price = price_val
                                logger.info(f"Parsed price {price_text} as {price_val}")
                        except ValueError as ve:
                            logger.error(f"Error parsing price {price_text}: {ve}")
                            continue

            if not price:
                price_patterns = [
                    r"From BRL[\s]*([\d.,]+)",
                    r"From €[\s]*([\d.,]+)"
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
                price_eur = price * BRL_TO_EUR_RATE
                logger.info(f"Found price for {flight_info}: {price:.2f} BRL ({price_eur:.2f} EUR)")
                return price, price_eur
            else:
                logger.error(f"Price not found for flight {flight_info}")
                return None, None

        except Exception as e:
            logger.error(f"Error finding price element for flight {flight_info}: {e}")
            await page.waitForFunction('document.body !== null && document.body.clientWidth > 0')
            await page.screenshot({'path': f'{DEBUG_DIR}/error_{flight_debug_id}.png', 'fullPage': True})
            html_content = await page.content()
            with open(f'{DEBUG_DIR}/page_error_{flight_debug_id}.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML content saved to {DEBUG_DIR}/page_error_{flight_debug_id}.html")
            return None, None

    except Exception as e:
        logger.exception(f"Error checking flight {flight_info}: {e}")
        return None, None