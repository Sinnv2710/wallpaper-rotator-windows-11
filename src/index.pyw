import os
import random
import requests
import time
from playwright.sync_api import sync_playwright
import time
import ctypes
import pygetwindow as gw
from PIL import Image
import threading
from pystray import Icon, Menu, MenuItem
from PIL import Image as PILImage, ImageDraw


TEMP_PATH = os.path.join("D:\\software\\script\\TEMP", "comic_wallpaper.jpg")
os.makedirs(os.path.dirname(TEMP_PATH), exist_ok=True)  # Ensure the directory exists
BASE_URL = "https://alphacoders.com/popular"
AUTO_REFRESH_INTERVAL_MINUTES = 30  # 🔁 Change every X minutes
# ✅ Move these up top before menu is created
auto_refresh_enabled = False
auto_refresh_thread = None

# Load the external icon image
ICON_PATH = os.path.join("D:\\software\\script\\src", "icon.jpg")

# Ensure the icon file exists
if not os.path.exists(ICON_PATH):
    raise FileNotFoundError(f"Icon file not found: {ICON_PATH}")

def hide_chrome_window():
    time.sleep(2)  # Give Chrome time to launch

    for window in gw.getAllWindows():
        title = window.title.lower()
        if "chrome" in title:
            print(f"Hiding: {window.title}")
            try:
                window.minimize()  # Minimize instead of .hide()
            except Exception as e:
                print(f"Could not hide window: {e}")

def get_full_image_url():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # ⚠️ Important: Use non-headless to bypass detection
             args=[
                        "--window-position=10000,10000",  # Offscreen
                        "--disable-background-timer-throttling",
                        "--disable-backgrounding-occluded-windows",
                        "--disable-renderer-backgrounding",
                    ],
            slow_mo=50,      # 👤 Simulate human interaction
            channel="chrome" # ✅ Use real Chrome install (if available)
        )
        context = browser.new_context()
        page = context.new_page()
        hide_chrome_window()  # Hides the Chrome window
        page.goto(BASE_URL, timeout=60000)
        

        # Scroll down slowly like a real human
        for _ in range(5):
            page.mouse.wheel(0, 800)
            page.wait_for_timeout(1000)

        # Pick a wallpaper
        links = page.locator('div.css-grid-content meta[itemprop="contentUrl"]').all()
        if not links:
            raise Exception("No wallpapers found.")

        chosen = random.choice(links)
        detail_url = chosen.get_attribute('content')
        print(f"Got: {detail_url}")

        browser.close()
        return detail_url

def set_wallpaper(image_url):
    print(f"Downloading: {image_url}")
    r = requests.get(image_url)
    with open(TEMP_PATH, 'wb') as f:
        f.write(r.content)

    # Re-encode image as clean RGB JPEG
    try:
        img = Image.open(TEMP_PATH).convert("RGB")
        img.save(TEMP_PATH, "JPEG")
        print("Re-encoded image for Windows compatibility.")
    except Exception as e:
        print(f"Failed to process image: {e}")

    # Apply wallpaper
    ctypes.windll.user32.SystemParametersInfoW(20, 0, TEMP_PATH, 3)
    print("Wallpaper set.")

def set_wallpaper_fit_mode():
    import winreg
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Control Panel\Desktop",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, "6")  # Fit
        winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, "0")   # No tile
        winreg.CloseKey(key)
        print("Wallpaper mode set to FIT.")
    except Exception as e:
        print(f"Failed to set wallpaper fit mode: {e}")

def change_wallpaper_async(icon=None, item=None):
    threading.Thread(target=set_wallpaper(get_full_image_url())).start()

def toggle_auto_refresh(icon, item):
    global auto_refresh_enabled, auto_refresh_thread

    auto_refresh_enabled = not auto_refresh_enabled

    # Recreate the menu with the updated auto-refresh status
    new_menu = Menu(
        MenuItem('Change Wallpaper Now', change_wallpaper_async),
        MenuItem(f'Auto-Refresh: {"ON" if auto_refresh_enabled else "OFF"}', toggle_auto_refresh, checked=lambda item: auto_refresh_enabled),
        MenuItem('Quit', quit_app)
    )
    icon.menu = new_menu  # Assign the new menu to the icon

    if auto_refresh_enabled and auto_refresh_thread is None:
        auto_refresh_thread = threading.Thread(target=auto_refresh_loop, daemon=True)
        auto_refresh_thread.start()

def auto_refresh_loop():
    global auto_refresh_enabled
    while auto_refresh_enabled:
        print(f"[🔁] Auto-refresh: changing wallpaper")
        set_wallpaper(get_full_image_url())
        for _ in range(AUTO_REFRESH_INTERVAL_MINUTES * 60):
            if not auto_refresh_enabled:
                print("[🛑] Auto-refresh stopped")
                return
            time.sleep(1)

def quit_app(icon, item):
    global auto_refresh_enabled
    auto_refresh_enabled = False
    icon.stop()

# Shared icon object
icon = Icon(
    "wallpaper_tray",
    icon=PILImage.open(ICON_PATH),  # Load the external icon image
    menu=Menu(
        MenuItem('Change Wallpaper Now', change_wallpaper_async),
        MenuItem('Auto-Refresh', toggle_auto_refresh, checked=lambda item: auto_refresh_enabled),
        MenuItem('Quit', quit_app)
    )
)

if __name__ == '__main__':
    threading.Thread(target=set_wallpaper(get_full_image_url())).start()  # Set once on startup
    icon.run()