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
CATEGORY_OPTION_XPATH = "//div[contains(text(),'Kategori')]"
CATEGORY_OPTION_2_XPATH = "//div[contains(text(),'TRİBÜN')]"
ALL_SEATS_XPATH = "//button[@id='custom_seat_button']"
OCCUPIED_SEAT_XPATH = "//*[@fill='#7691a7']"
AVAILABLE_SEAT_XPATH = "//*[@fill='#ffffff']"

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

end_category = False

# Seat info (away)
AWAY_CATEGORY = "//span[contains(text(),'MİSAFİR')]"
AWAY_BLOCK = "//option[contains(text(),'GÜNEY')]"

# Team info
away = False
OPPONENT = "Sakaryaspor"

if away:
    match = f"{OPPONENT} - Kocaelispor"
    title = "Deplasman satılan bilet"
else:
    match = f"Kocaelispor - {OPPONENT}"
    title = "Satılan bilet"

URL = "https://www.passo.com.tr/tr/etkinlik/kocaelispor-sakaryaspor-trendyol-lig-mac-bileti-passo/8067331"

def wait_until_element(driver, xpath):
    return WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, xpath)))

with SB(uc=True) as driver:
    driver.maximize_window()
    driver.open(URL)
    driver.sleep(2)
    driver.execute_script("window.scrollBy(0,550)")

    # Click "SATIN AL"
    wait_until_element(driver, BUY_BTN_XPATH).click()
    driver.sleep(2)
    
    # Login
    wait_until_element(driver, EMAIL_INPUT_XPATH).send_keys(EMAIL)
    wait_until_element(driver, PASSWORD_INPUT_XPATH).send_keys(PASSWORD)
    # wait_until_element(driver, CAPTCHA_CHECKBOX_XPATH).click() + Keys.ENTER
    pyautogui.click(675, 720)
    driver.sleep(1)
    wait_until_element(driver, LOGIN_BTN_XPATH).click()

    total_occupied_seats = 0
    total_available_seats = 0
    home_total = 31827
        
    for category, blocks in zip(home_cat, home_block):
        try:
        # Select category
            if end_category:
                wait_until_element(driver, CATEGORY_OPTION_2_XPATH).click()
                end_category = False
                driver.sleep(10)
            else:
                wait_until_element(driver, CATEGORY_OPTION_XPATH).click()
            wait_until_element(driver, category).click()
            
            for i, block in enumerate(blocks):
                try:
                    # Select the next block
                    block_xpath = f"//option[contains(text(),'{block}')]"
                    wait_until_element(driver, block_xpath).click()

                    # Open seat map of the selected block
                    wait_until_element(driver, ALL_SEATS_XPATH).click()
                    driver.sleep(5)

                    # Count all seats in the block
                    occupied_seats = driver.find_elements(By.XPATH, OCCUPIED_SEAT_XPATH)
                    available_seats = driver.find_elements(By.XPATH, AVAILABLE_SEAT_XPATH)

                    total_occupied_seats += len(occupied_seats)
                    total_available_seats += len(available_seats)

                    # Refresh the page
                    driver.execute_script("window.location.reload()")
                    driver.sleep(2) 

                    # Select the category again
                    wait_until_element(driver, CATEGORY_OPTION_XPATH).click()
                    wait_until_element(driver, category).click()

                    # Check if this is the last block in the category
                    if i == len(blocks) - 1:
                        end_category = True
                        break
                except Exception as e:
                    continue
        except Exception as e:
            continue
    
    # Calculate & Print Results
    total_count = total_occupied_seats + total_available_seats
    full_blocks = home_total - total_count
    total_occupied_seats += full_blocks
    occupancy_rate = (total_occupied_seats / home_total) * 100 if total_count > 0 else 0

    bar_length = int(occupancy_rate / 6.25)
    empty_length = 16 - bar_length
    occupancy_bar = "█" * bar_length + "░" * empty_length

    output = f"{match}\n1. Lig tribün doluluk oranı\n{occupancy_bar} %{occupancy_rate:.2f}\n{title}: {total_occupied_seats} / {home_total}"
    if occupancy_rate == 100:
        output += "\n🔥 KAPALI GİŞE"
    else:
        output += f" (Kalan: {total_available_seats})"
    print(output)
