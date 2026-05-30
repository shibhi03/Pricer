import glob
import os
import re
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import SessionNotCreatedException
from webdriver_manager.chrome import ChromeDriverManager

def _chromedriver_version_key(path: str) -> tuple:
    match = re.search(r"win64[\\/](\d+)\.(\d+)\.(\d+)\.(\d+)", path.replace("\\", "/"))
    if match:
        return tuple(int(part) for part in match.groups())
    return (0, 0, 0, 0)

def _find_cached_chromedriver() -> str | None:
    wdm_root = os.path.expanduser("~/.wdm")
    candidates = glob.glob(os.path.join(wdm_root, "**", "chromedriver.exe"), recursive=True)
    if not candidates:
        return None
    return max(candidates, key=_chromedriver_version_key)

def _get_chrome_service(config, *, use_cache_only=False):
    chrome_driver_path = config.get("chrome_driver_path")
    if chrome_driver_path:
        chrome_driver_path = os.path.expanduser(chrome_driver_path)
        if os.path.isfile(chrome_driver_path):
            return Service(chrome_driver_path)
        print(f"[driver] chrome_driver_path invalid or missing: {chrome_driver_path}. Falling back to cached driver.")

    cached_driver = _find_cached_chromedriver()
    if cached_driver:
        return Service(cached_driver)

    if use_cache_only:
        raise FileNotFoundError("No cached ChromeDriver found under ~/.wdm")

    driver_path = ChromeDriverManager().install()
    return Service(driver_path)

def create_driver(config):
    browser_config = config["browser"]

    options = Options()

    # Setting headless mode
    if browser_config.get("headless", False):
        options.add_argument("--headless=new")

    # Choosing a random user agent from the list
    user_agents = browser_config.get("user_agents", [])
    if user_agents:
        user_agent = random.choice(user_agents)
        print(f"Using user agent: {user_agent}")
        options.add_argument(f"user-agent={user_agent}")

    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    try:
        driver = webdriver.Chrome(options=options)
    except (OSError, SessionNotCreatedException):
        service = _get_chrome_service(config)
        try:
            driver = webdriver.Chrome(service=service, options=options)
        except (OSError, SessionNotCreatedException) as e:
            print(f"[driver] ChromeDriver failed ({e}). Retrying with latest cached driver.")
            service = _get_chrome_service(config, use_cache_only=True)
            driver = webdriver.Chrome(service=service, options=options)

    driver.set_page_load_timeout(browser_config.get("page_load_timeout", 30))
    driver.implicitly_wait(browser_config.get("implicit_wait", 5))

    return driver