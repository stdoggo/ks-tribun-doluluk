import os
from dotenv import load_dotenv
from seleniumbase import SB
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyautogui

load_dotenv(dotenv_path='../ks-tribun-doluluk/keys.env')
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

# XPaths
BUY_BTN_XPATH = "//button[text()= 'SATIN AL']"
LOGIN_BTN_XPATH = "//button[@class='black-btn']"
EMAIL_INPUT_XPATH = "//input[@placeholder='E-Posta Adresi']"
PASSWORD_INPUT_XPATH = "//input[@placeholder='Şifre']"
CAPTCHA_CHECKBOX_XPATH = "//*[contains(@id, 'cf-chl-widget-')]"
CATEGORY_OPTION_XPATH = "//*[@id='blocks']"
SEAT_MAP_XPATH = "//button[@id='custom_seat_button']"
ALL_SEATS_XPATH = "//*[@class='seat']"
OCCUPIED_SEAT_XPATH = "//*[@fill='#7691a7']"
AVAILABLE_SEAT_XPATH = "//*[@fill='#ffffff']"
CHANGE_SEAT_XPATH = "//button[contains(text(),'Seçimi değiştir')]"

# Seat info (home)
home_cat = [
    "//span[contains(text(),'NUMARALI ALT')]", "//span[contains(text(),'NUMARALI ÜST')]",
    "//span[contains(text(),'MARATON ALT')]", "//span[contains(text(),'MARATON ÜST')]",
    "//span[contains(text(),'GÜNEY KALE ARKASI ALT')]", "//span[contains(text(),'GÜNEY KALE ARKASI ÜST')]",
    "//span[contains(text(),'KUZEY KALE ARKASI ALT')]", "//span[contains(text(),'KUZEY KALE ARKASI ÜST')]"
]

home_block = [
    ["111-A", "111-B", "112", "113", "114", "115", "116"],
    ["313", "314", "315-A", "315-B"],
    ["101", "102", "103", "124-A", "124-B", "125", "126"],
    ["301", "302", "303 DOĞU", "324 DOĞU", "325", "326"],
    ["204-A", "204-B", "205", "206", "207", "208", "209", "210"],
    ["303 GÜNEY", "304", "305", "306", "307", "308", "309", "310", "311", "312"],
    ["217-A", "217-B", "218", "219", "220", "221", "222", "223"],
    ["318-B", "319", "320", "321", "322", "323", "324 KUZEY"]
]

# Seat info (away)
AWAY_CATEGORY = "//span[contains(text(),'MİSAFİR')]"
AWAY_BLOCK = "//option[contains(text(),'GÜNEY')]"

# Match info
AWAY = False
OPPONENT = "Sakaryaspor"

match_title = f"Kocaelispor - {OPPONENT}" if not AWAY else f"{OPPONENT} - Kocaelispor"
ticket_title = "Satılan bilet" if not AWAY else "Deplasman satılan bilet"

URL = "https://www.passo.com.tr/tr/etkinlik/kocaelispor-sakaryaspor-trendyol-lig-mac-bileti-passo/8067331"

def select_element(driver, xpath, timeout=60):
    return WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, xpath)))

def login(driver):
    select_element(driver, EMAIL_INPUT_XPATH).send_keys(EMAIL)
    select_element(driver, PASSWORD_INPUT_XPATH).send_keys(PASSWORD)
    driver.sleep(1)
    pyautogui.click(675, 720)
    driver.sleep(1)
    select_element(driver, LOGIN_BTN_XPATH).click()

def count_seats(driver):
    total_occupied = 0
    total_count = 0
    
    for category, blocks in zip(home_cat, home_block):
        try:
        # Select category
            driver.sleep(1)
            driver.execute_script("window.scrollBy(0,300)")
            select_element(driver, CATEGORY_OPTION_XPATH).click()
            select_element(driver, category).click()
            
            for block in blocks:
                try:
                    # Select the next block
                    driver.sleep(1)
                    driver.execute_script("window.scrollBy(0,250)")
                    block_xpath = f"//option[contains(text(),'{block}')]"
                    select_element(driver, block_xpath).click()

                    # Open seat map of the selected block
                    select_element(driver, SEAT_MAP_XPATH).click()
                    driver.sleep(5)

                    # Count all seats in the block
                    total = driver.find_elements(By.XPATH, ALL_SEATS_XPATH)
                    occupied = driver.find_elements(By.XPATH, OCCUPIED_SEAT_XPATH)
                    
                    total_count += len(total)
                    total_occupied += len(occupied)
                    
                    # Change the block
                    select_element(driver, CHANGE_SEAT_XPATH).click()

                except Exception as error:
                    print(f"Blok dolu: {block}\n{error}")
                    continue
        except Exception as error:
            print(f"Kategori dolu: {category}\n{error}")
            continue
        
    return total_count, total_occupied

def main():
    with SB(uc=True) as driver:
        driver.maximize_window()
        driver.open(URL)
        driver.sleep(2)
        driver.execute_script("window.scrollBy(0,550)")

        # Click "SATIN AL"
        select_element(driver, BUY_BTN_XPATH).click()
        driver.sleep(2)
        
        # Login
        login(driver)

        # Count all seats
        driver.execute_script("document.body.style.zoom='80%'")
        total_count, total_occupied = count_seats(driver)
        
        # Calculate and print the result
        HOME_TOTAL = 31827
        total_available = total_count - total_occupied
        full_blocks = HOME_TOTAL - total_count
        total_occupied += full_blocks
        occupancy_rate = (total_occupied / HOME_TOTAL) * 100

        bar_length = int(occupancy_rate / 6.25)
        empty_length = 16 - bar_length
        occupancy_bar = "█" * bar_length + "░" * empty_length

        output = f"{match_title}\n{occupancy_bar} %{occupancy_rate:.2f}\n{ticket_title}: {total_occupied:,} / {HOME_TOTAL:,}"
        if occupancy_rate == 100:
            output += "\n🔥 KAPALI GİŞE"
        else:
            output += f" (Kalan: {total_available:,})"
            
    return output

if __name__ == "__main__":
    print(main())
