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
import win32con
import win32gui
import win32api
import win32process
import json
import threading

# Base path of the current script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Temporary image path
TEMP_PATH = os.path.join(BASE_DIR, "TEMP", "comic_wallpaper.jpg")
print(TEMP_PATH)
os.makedirs(os.path.dirname(TEMP_PATH), exist_ok=True)

auto_refresh_enabled = False
auto_refresh_thread = None
SETTINGS_PATH = os.path.join(BASE_DIR,"settings.json")
AUTO_REFRESH_INTERVAL_MINUTES = 30  # 🔁 Change every X minutes
# Load the external icon image
ICON_PATH = os.path.join(BASE_DIR,"icon.jpg")
BASE_URL_DEFAULT = "https://alphacoders.com/popular"
current_base_url = BASE_URL_DEFAULT
# Ensure the icon file exists
if not os.path.exists(ICON_PATH):
    raise FileNotFoundError(f"Icon file not found: {ICON_PATH}")

def hide_chrome_window_loop():
    def enum_and_hide():
        while True:
            found = False
            def handler(hwnd, _):
                nonlocal found
                title = win32gui.GetWindowText(hwnd).lower()
                if "chrome" in title:
                    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                    ex_style &= ~win32con.WS_EX_APPWINDOW
                    ex_style |= win32con.WS_EX_TOOLWINDOW
                    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
                    win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
                    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                    found = True

            win32gui.EnumWindows(handler, None)
            if found:
                break
            time.sleep(0.1)

    threading.Thread(target=enum_and_hide, daemon=True).start()

def load_settings():
    global current_base_url
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r") as f:
                data = json.load(f)
                current_base_url = data.get("base_url", BASE_URL_DEFAULT)
                print(f"[⚙️] Loaded base URL: {current_base_url}")
        except Exception as e:
            print(f"[⚠️] Failed to load settings: {e}")
    else:
        print(f"[ℹ️] No settings file found. Using default.")

def save_settings():
    try:
        with open(SETTINGS_PATH, "w") as f:
            json.dump({"base_url": current_base_url}, f, indent=2)
            print(f"[💾] Saved base URL: {current_base_url}")
    except Exception as e:
        print(f"[❌] Failed to save settings: {e}")

def hide_chrome_from_taskbar():
    def enum_handler(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd).lower()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if "chrome" in title:
                print(f"[🪄] Found Chrome window: {title}")
                ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                ex_style &= ~win32con.WS_EX_APPWINDOW
                ex_style |= win32con.WS_EX_TOOLWINDOW
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
                win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
    win32gui.EnumWindows(enum_handler, None)

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

def prevent_focus_stealing():
    def enum_handler(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "chrome" in title.lower():
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                win32gui.SetWindowPos(hwnd, win32con.HWND_BOTTOM, 0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
    win32gui.EnumWindows(enum_handler, None)

def get_full_image_url():
    with sync_playwright() as p:
        hide_chrome_window_loop()
        browser = p.chromium.launch(
            headless=False,  # ⚠️ Important: Use non-headless to bypass detection
             args=[
                    "--window-position=32000,32000",       # Move far offscreen
                    "--window-size=1,1",                   # Tiny window
                    "--disable-gpu",                       # Disable GPU rendering
                    "--disable-software-rasterizer",
                    "--disable-dev-shm-usage",
                    "--disable-infobars",
                    "--disable-extensions",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                    "--mute-audio",
                    ],
            slow_mo=50,      # 👤 Simulate human interaction
            channel="chrome" # ✅ Use real Chrome install (if available)
        )
        context = browser.new_context()
        page = context.new_page()
        hide_chrome_window()  # Hides the Chrome window
        page.goto(current_base_url, timeout=60000)
        hide_chrome_from_taskbar()
        prevent_focus_stealing()  # Prevents focus stealing
        page.wait_for_timeout(2000)  # Wait for the page to load
        

        # Scroll down slowly like a real human
        for _ in range(10):
            page.mouse.wheel(0, 800)
            page.wait_for_timeout(1000)

        # Pick a wallpaper
        links = page.locator('meta[itemprop="contentUrl"]').all()
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
    MenuItem('Change Source URL', prompt_new_base_url),
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

def prompt_new_base_url(icon, item):
    import tkinter as tk
    from tkinter import simpledialog

    def run_input_popup():
        global current_base_url
        root = tk.Tk()
        root.withdraw()
        new_url = simpledialog.askstring("Change Base URL", "Enter new URL:", initialvalue=current_base_url)
        if new_url:
            current_base_url = new_url
            save_settings()
            print(f"[🔧] New Base URL set: {current_base_url}")
        root.destroy()

    threading.Thread(target=run_input_popup).start()

# Shared icon object
icon = Icon(
    "wallpaper_tray",
    icon=PILImage.open(ICON_PATH),  # Load the external icon image
    menu=Menu(
    MenuItem('Change Wallpaper Now', change_wallpaper_async),
    MenuItem('Custom Source URL', prompt_new_base_url),
    MenuItem('Auto-Refresh', toggle_auto_refresh, checked=lambda item: auto_refresh_enabled),
    MenuItem('Quit', quit_app)
    )
)

if __name__ == '__main__':
    load_settings()
    threading.Thread(target=set_wallpaper(get_full_image_url())).start()  # Set once on startup
    icon.run()