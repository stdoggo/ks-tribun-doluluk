import os
from dotenv import load_dotenv
from seleniumbase import SB
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pyautogui

MATCH_TITLE_XPATH = "//div[@class='r-title']"
MATCH_DATE_XPATH = "//span[@class='r-date']"
MATCH_TIME_XPATH = "//span[@class='r-date']/div"
MATCH_URL_XPATH = "//div[@class='wrapper row event-search-items']/div[1]/div/div/div[2]"

URL = "https://www.passo.com.tr/tr/ara?searchQuery=Kocaelispor&etkinlikdetayi=true"

# Match info
AWAY = False
OPPONENT = "Sakaryaspor"

home_or_away = f"Kocaelispor - {OPPONENT}" if not AWAY else f"{OPPONENT} - Kocaelispor"
ticket_title = "Satılan bilet" if not AWAY else "Deplasman satılan bilet"

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
chrome_options = Options()
chrome_options.add_argument(f"user-agent={user_agent}")

def select_element(driver, xpath, timeout=60):
    return WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, xpath)))

with SB(uc=True) as driver:
    driver.driver_options = chrome_options
    driver.maximize_window()
    driver.open(URL)
    driver.sleep(5)
    match_title = driver.find_element(By.XPATH, MATCH_TITLE_XPATH)
    match_date = driver.find_element(By.XPATH, MATCH_DATE_XPATH)
    #match_time = driver.find_element(By.XPATH, MATCH_TIME_XPATH)
    print(f"Maç: {match_title.text}\nTarih: {match_date.text}") # \nTarih: {match_date.text}\nSaat: {match_time.text}
    select_element(driver, MATCH_URL_XPATH).click()
    driver.sleep(2)