from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import random

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

    service = Service(config["chrome_driver_path"])

    # Creatind the driver
    driver = webdriver.Chrome(
        service = service,
        options = options
    )

    driver.set_page_load_timeout(browser_config.get("page_load_timeout", 30))
    driver.implicitly_wait(browser_config.get("implicit_wait", 5))

    return driver