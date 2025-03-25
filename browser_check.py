#!/usr/bin/env python3
"""
This script checks for the presence of a compatible Chrome/Chromium browser
and the pyppeteer library. It also checks system resources and attempts to
launch a browser instance to verify everything is working correctly.
It is designed to be run in a Python 3 environment.
It checks for:
- Chrome/Chromium installation
- pyppeteer installation
- System resources (RAM, CPU)
- Sandbox configuration
- Test browser launch

uv run python booking.py

"""
import os
import sys
import asyncio
import subprocess
import platform
import shutil

try:
    import psutil
except ImportError:
    print("psutil not installed. Install with: pip install psutil")
    psutil = None

async def check_browser():
    print("\n=== Chrome/Chromium Browser Check ===\n")
    
    # Check if a compatible browser is installed
    possible_paths = [
        '/usr/bin/chromium-browser',
        '/usr/bin/chromium',
        '/usr/bin/chrome',
        '/usr/bin/google-chrome',
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    ]
    
    browser_path = None
    for path in possible_paths:
        if os.path.exists(path):
            browser_path = path
            print(f"✅ Found browser at: {browser_path}")
            break
    
    if not browser_path:
        print("❌ No Chrome/Chromium browser found in common locations")
        print("Please install Chrome or Chromium browser")
    else:
        try:
            result = subprocess.run([browser_path, "--version"], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   text=True)
            print(f"Browser version: {result.stdout.strip()}")
        except Exception as e:
            print(f"❌ Error getting browser version: {e}")
    
    # Check for pyppeteer installation
    try:
        from pyppeteer import __version__
        print(f"✅ pyppeteer version: {__version__}")
        
        try:
            from pyppeteer.chromium_downloader import chromium_executable
            default_executable = chromium_executable()
            print(f"pyppeteer chromium path: {default_executable}")
            if os.path.exists(default_executable):
                print("✅ pyppeteer's Chromium exists")
            else:
                print("❌ pyppeteer's Chromium doesn't exist - may need to download")
                print("Run: python -c 'import pyppeteer.chromium_downloader; pyppeteer.chromium_downloader.download_chromium()'")
        except Exception as e:
            print(f"❌ Error checking pyppeteer's Chromium: {e}")
            
    except ImportError:
        print("❌ pyppeteer not installed. Install with: pip install pyppeteer")
    
    # Check system resources
    print("\n=== System Resources ===\n")
    print(f"OS: {platform.system()} {platform.release()}")
    
    if psutil:
        mem = psutil.virtual_memory()
        print(f"RAM: {mem.total / (1024**3):.1f} GB total, {mem.available / (1024**3):.1f} GB available")
        print(f"CPU: {psutil.cpu_count(logical=False)} physical cores, {psutil.cpu_count()} logical cores")
        print(f"Current CPU usage: {psutil.cpu_percent()}%")
    else:
        print("Install psutil for more detailed system information")
    
    # Check for sandbox compatibility
    print("\n=== Sandbox Configuration ===\n")
    if platform.system() == "Linux":
        try:
            with open("/proc/sys/kernel/unprivileged_userns_clone", "r") as f:
                userns = f.read().strip()
                if userns == "1":
                    print("✅ User namespaces enabled (good for sandboxing)")
                else:
                    print("❌ User namespaces disabled (may need --no-sandbox)")
        except:
            print("Could not check user namespace configuration")
    
    # Attempt a test launch
    print("\n=== Test Browser Launch ===\n")
    try:
        from pyppeteer import launch
        print("Attempting to launch browser...")
        
        browser = await launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        print("✅ Browser launched successfully!")
        
        version = await browser.version()
        print(f"Browser version: {version}")
        
        await browser.close()
        print("Browser closed successfully")
    except Exception as e:
        print(f"❌ Browser launch failed: {e}")
        print("\nSuggested fixes:")
        print("1. Install/reinstall Chrome or Chromium browser")
        print("2. Try: pip uninstall pyppeteer && pip install pyppeteer")
        print("3. Try alternative: pip install playwright && playwright install chromium")
    
    print("\nDiagnostic check complete")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(check_browser())
