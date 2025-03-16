import os
from dotenv import load_dotenv
from seleniumbase import SB
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyautogui

# Load environment variables
load_dotenv(dotenv_path='../ks-tribun-doluluk/keys.env')
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

# XPaths
XPATHS = {
    "buy_button": "//button[text()='SATIN AL']",
    "login_button": "//button[@class='black-btn']",
    "email_input": "//input[@placeholder='E-Posta Adresi']",
    "password_input": "//input[@placeholder='Şifre']",
    "captcha_checkbox": "//*[contains(@id, 'cf-chl-widget-')]",
    "category_option": "//div[contains(text(),'Kategori')]",
    "category_tribune": "//div[contains(text(),'TRİBÜN')]",
    "all_seats": "//button[@id='custom_seat_button']",
    "occupied_seat": "//*[@fill='#7691a7']",
    "available_seat": "//*[@fill='#ffffff']"
}

# Seat info using dictionary
HOME_SECTIONS = {
    "NUMARALI ALT": ["111-A", "111-B", "112", "113", "114", "115", "116"],
    "NUMARALI ÜST": ["313", "314", "315-A", "315-B"],
    "MARATON ALT": ["101", "102", "103", "124-A", "124-B", "125", "126"],
    "MARATON ÜST": ["301", "302", "303 DOĞU", "324 DOĞU", "325", "326"],
    "GÜNEY KALE ARKASI ALT": ["204-A", "204-B", "205", "206", "207", "208", "209", "210"],
    "GÜNEY KALE ARKASI ÜST": ["303 GÜNEY", "304", "305", "306", "307", "308", "309", "310", "311", "312"],
    "KUZEY KALE ARKASI ALT": ["217-A", "217-B", "218", "219", "220", "221", "222", "223"],
    "KUZEY KALE ARKASI ÜST": ["318-B", "319", "320", "321", "322", "323", "324 KUZEY"]
}

# Match details
AWAY_MODE = False
OPPONENT = "Sakaryaspor"

match_title = f"Kocaelispor - {OPPONENT}" if not AWAY_MODE else f"{OPPONENT} - Kocaelispor"
ticket_title = "Satılan bilet" if not AWAY_MODE else "Deplasman satılan bilet"
URL = "https://www.passo.com.tr/tr/etkinlik/kocaelispor-sakaryaspor-trendyol-lig-mac-bileti-passo/8067331"

# Max seats
HOME_TOTAL = 31827

# Function to select an element
def select_element(driver, xpath, timeout=60):
    return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))

# Function to login
def login(driver):
    select_element(driver, XPATHS["email_input"]).send_keys(EMAIL)
    select_element(driver, XPATHS["password_input"]).send_keys(PASSWORD)
    driver.sleep(1)
    pyautogui.click(675, 720)  # Solve CAPTCHA manually if required
    driver.sleep(1)
    select_element(driver, XPATHS["login_button"]).click()

# Function to process seats
def process_seats(driver):
    total_occupied = 0
    total_available = 0
    for category, blocks in HOME_SECTIONS.items():
        try:
            select_element(driver, XPATHS["category_option"]).click()
            select_element(driver, f"//span[contains(text(),'{category}')]").click()
            
            for block in blocks:
                try:
                    block_xpath = f"//option[contains(text(),'{block}')]"
                    select_element(driver, block_xpath).click()
                    select_element(driver, XPATHS["all_seats"]).click()
                    driver.sleep(3)

                    occupied = len(driver.find_elements(By.XPATH, XPATHS["occupied_seat"]))
                    available = len(driver.find_elements(By.XPATH, XPATHS["available_seat"]))

                    total_occupied += occupied
                    total_available += available

                except Exception as e:
                    print(f"Error processing block {block}: {e}")
                    continue
        except Exception as e:
            print(f"Error selecting category {category}: {e}")
            continue
    
    return total_occupied, total_available

# Main script execution
with SB(uc=True) as driver:
    driver.maximize_window()
    driver.open(URL)
    driver.sleep(2)
    driver.execute_script("window.scrollBy(0,550)")
    
    # Click "SATIN AL"
    select_element(driver, XPATHS["buy_button"]).click()
    driver.sleep(2)
    
    # Login
    login(driver)

    # Process seating info
    occupied_seats, available_seats = process_seats(driver)

    # Calculate and display results
    total_count = occupied_seats + available_seats
    full_blocks = TOTAL_SEATS - total_count
    occupied_seats += full_blocks
    occupancy_rate = (occupied_seats / HOME_TOTAL) * 100 if total_count > 0 else 0

    bar_length = int(occupancy_rate / 6.25)
    empty_length = 16 - bar_length
    occupancy_bar = "█" * bar_length + "░" * empty_length

    output = f"{match_title}\n{occupancy_bar} %{occupancy_rate:.2f}\n{ticket_title}: {occupied_seats} / {TOTAL_SEATS}"
    output += "\n🔥 KAPALI GİŞE" if occupancy_rate == 100 else f" (Kalan: {available_seats})"
    
    print(output)
