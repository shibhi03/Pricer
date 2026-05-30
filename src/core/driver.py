import glob
import os
import re
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import SessionNotCreatedException
from webdriver_manager.chrome import ChromeDriverManager

_INVALID_CHROMEDRIVER_NAMES = (
    "THIRD_PARTY_NOTICES.chromedriver",
    "LICENSE.chromedriver",
)

def _chromedriver_version_key(path: str) -> tuple:
    match = re.search(r"win64[\\/](\d+)\.(\d+)\.(\d+)\.(\d+)", path.replace("\\", "/"))
    if match:
        return tuple(int(part) for part in match.groups())
    return (0, 0, 0, 0)

_CHROMEDRIVER_NAMES = ("chromedriver.exe", "chromedriver")

def _is_valid_chromedriver(path: str) -> bool:
    if not path or not os.path.isfile(path):
        return False
    if os.path.basename(path).lower() not in _CHROMEDRIVER_NAMES:
        return False
    if any(bad in path for bad in _INVALID_CHROMEDRIVER_NAMES):
        return False
    # Real chromedriver binaries are megabytes; notice files are tiny.
    return os.path.getsize(path) > 500_000

def _resolve_chromedriver_path(path: str) -> str | None:
    """Map webdriver-manager output (sometimes a notice file) to chromedriver."""
    if _is_valid_chromedriver(path):
        return path

    search_root = path if os.path.isdir(path) else os.path.dirname(path)
    if not search_root:
        return None

    for root, _, files in os.walk(search_root):
        for name in files:
            if name.lower() in _CHROMEDRIVER_NAMES:
                candidate = os.path.join(root, name)
                if _is_valid_chromedriver(candidate):
                    return candidate
    return None

def apply_chrome_runtime(options: Options) -> Options:
    """Apply container/local Chrome paths (e.g. Docker / Cloud Run)."""
    chrome_bin = os.environ.get("CHROME_BIN")
    if chrome_bin and os.path.isfile(chrome_bin):
        options.binary_location = chrome_bin
    return options

def _find_cached_chromedriver() -> str | None:
    wdm_root = os.path.expanduser("~/.wdm")
    candidates = []
    for pattern in ("**/chromedriver.exe", "**/chromedriver"):
        candidates.extend(glob.glob(os.path.join(wdm_root, pattern), recursive=True))
    candidates = [p for p in candidates if _is_valid_chromedriver(p)]
    if not candidates:
        return None
    return max(candidates, key=_chromedriver_version_key)

def _get_chrome_service(config, *, use_cache_only=False):
    env_driver = os.environ.get("CHROMEDRIVER_PATH")
    if env_driver and os.path.isfile(env_driver):
        return Service(env_driver)

    chrome_driver_path = config.get("chrome_driver_path")
    if chrome_driver_path:
        resolved = _resolve_chromedriver_path(os.path.expanduser(chrome_driver_path))
        if resolved:
            return Service(resolved)
        print(f"[driver] chrome_driver_path invalid or missing: {chrome_driver_path}. Falling back to cached driver.")

    cached_driver = _find_cached_chromedriver()
    if cached_driver:
        return Service(cached_driver)

    if use_cache_only:
        raise FileNotFoundError("No cached ChromeDriver found under ~/.wdm")

    installed = ChromeDriverManager().install()
    resolved = _resolve_chromedriver_path(installed)
    if not resolved:
        raise FileNotFoundError(
            f"ChromeDriverManager returned an invalid path ({installed}). "
            "Delete %USERPROFILE%\\.wdm and run again, or set chrome_driver_path in config.yaml."
        )
    return Service(resolved)

def create_driver(config):
    browser_config = config["browser"]

    options = apply_chrome_runtime(Options())

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

    def _start_with_service(service):
        return webdriver.Chrome(service=service, options=options)

    try:
        driver = webdriver.Chrome(options=options)
    except (OSError, SessionNotCreatedException):
        service = _get_chrome_service(config)
        try:
            driver = _start_with_service(service)
        except (OSError, SessionNotCreatedException) as e:
            winerr = getattr(e, "winerror", None)
            if winerr == 193 or "not a valid Win32 application" in str(e):
                print("[driver] Invalid ChromeDriver binary (WinError 193). Using cached chromedriver.exe.")
            else:
                print(f"[driver] ChromeDriver failed ({e}). Retrying with cached driver.")
            service = _get_chrome_service(config, use_cache_only=True)
            driver = _start_with_service(service)

    driver.set_page_load_timeout(browser_config.get("page_load_timeout", 30))
    driver.implicitly_wait(browser_config.get("implicit_wait", 5))

    return driver