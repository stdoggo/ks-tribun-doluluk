import os
import time
import pytz
import requests
import pyautogui
import locale
from requests.exceptions import RequestException
from contextlib import redirect_stdout
from dotenv import load_dotenv
from datetime import datetime
from seleniumbase import SB
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

# Login credentials
load_dotenv(dotenv_path='keys.env')

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Date of the data
timezone = pytz.timezone("Europe/Istanbul")
current_date = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")

# URL
URL = "https://www.passo.com.tr/tr/ara?searchQuery=Kocaelispor&etkinlikdetayi=true"

# XPaths
XPATHS = {
    "BUY_BUTTON": "//button[text()= 'SATIN AL']",
    "LOGIN_BUTTON": "//button[@class='black-btn']",
    "EMAIL_INPUT": "//input[@placeholder='E-Posta Adresi']",
    "PASSWORD_INPUT": "//input[@placeholder='Şifre']",
    "CATEGORY_DROPDOWN": "//div[@id='blocks']",
    "CATEGORY_OPTIONS": "//div[@class='dropdown-options']/div",
    "DISABLED_OPTION": "//div[@class='dropdown-options']/div[@class='dropdown-option disabled']",
    "BLOCK_DROPDOWN": "//select[@id='blocks']",
    "BLOCK_OPTIONS": "//select[@id='blocks']/option",
    "NULL_OPTION": "//select[@id='blocks']/option[contains(text(),'Blok Seçiniz')]",
    "SEAT_MAP": "//button[@id='custom_seat_button']",
    "ALL_SEATS": "//*[@class='seats']/*[@class='seat']",
    "OCCUPIED_SEATS": "//*[@class='seats']/*[@class='seat']/*[@fill='#7691a7']",
    "AVAILABLE_SEATS": "//*[@fill='#ffffff']",
    "CHANGE_SEAT": "//button[contains(text(),'Seçimi değiştir')]",
    "MATCH_TITLE": "//div[@class='r-title']",
    "MATCH_DATE": "//span[@class='r-date']",
    "MATCH_TIME": "//span[@class='r-date']/div",
    "MATCH_URL": f"//div[contains(text(),'Kocaelispor')]",
    "NO_SEATS_POPUP": "//button[contains(text(),'Tamam')]",
    "COOKIE_MESSAGE": "//a[@aria-label='dismiss cookie message']",
    "NO_MATCH": "//*[contains(text(),'mevcut bir etkinlik bulunmamaktadır')]",
    "PRIORITY": "//div[@class='r-title' and contains(text(),'Kongre')]"
}
    
# Wait for the element to load
def wait_element(driver, xpath, timeout=60):
    return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))

# Wait for dropdown menu options to load
def wait_options(driver, xpath, timeout=60):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))

def wait_scroll(driver, xpath, timeout=60):
    element = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
    driver.execute_script("arguments[0].scrollIntoView(true);", element)
    return element

# Click element with the try-except block
def safe_click(driver, xpath):
    try:
        wait_element(driver, xpath).click()
    except Exception:
        pass

# Check if there is no match available
def check_if_no_match(xpath):
    try:
        xpath = wait_element(By.XPATH, xpath)
        if xpath.is_displayed():
            return "Maç bulunamadı."
    except:
        pass

# Shorten github URL
def shorten_url(long_url):
    response = requests.get(f"http://tinyurl.com/api-create.php?url={long_url}")
    if response.status_code == 200:
        return response.text
    return None

# Upload output.txt to Github
def upload_to_gist():
    filename = "output.txt"
    description = f"Blok doluluk durumu ({current_date})"
    public = True

    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()

    payload = {
        "description": description,
        "public": public,
        "files": {
            filename: {
                "content": content
            }
        }
    }

    try:
        response = requests.post(
            "https://api.github.com/gists",
            json=payload,
            headers={
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json"
            }
        )

        if response.status_code == 201:
            gist_data = response.json()
            raw_url = list(gist_data["files"].values())[0]["raw_url"]
            short_url = shorten_url(raw_url)
            return short_url
        else:
            print(f"Hata kodu: {response.status_code}")
            print(f"{response.text}")
            return None
    except RequestException as error:
        print(f"Hata: {error}")
        return None

# Extract opponent name
def extract_clubs(filename="club_list.txt"):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return [line.strip() for line in file.readlines()]
    except OSError as error:
        print(f"Dosya okunamadı\n{error}")

def extract_match_details(driver):
    try:
        # Find match and extract the opponent details
        clubs = extract_clubs()
        match_text = wait_element(driver, XPATHS["MATCH_TITLE"]).text
        opponent = next((club for club in clubs if club in match_text), "Takım bulunamadı")
        if "Spor" in opponent:
            opponent = opponent.replace("Spor", "spor").replace(" ", "")

        # Find out if it's home or away game
        AWAY = match_text.split(" - ")[0].strip() != "Kocaelispor"

        # Extract match details
        locale.setlocale(locale.LC_TIME, "tr_TR.UTF-8")
        match_date_str = wait_element(driver, XPATHS["MATCH_DATE"]).text.replace("\n", " ")
        match_date = datetime.strptime(match_date_str, '%d %b %Y %H:%M').strftime('%Y-%m-%d %H:%M')

        match_title = f"Kocaelispor - {opponent}" if not AWAY else f"{opponent} - Kocaelispor"
        ticket = "Satılan bilet" if not AWAY else "Deplasman satılan bilet"

        return match_title, match_date, ticket, AWAY
    except Exception:
        return None
    
# Sign in passo.com.tr
def login(driver, attempts=5, delay=20):
    for i in range(attempts):
        try:
            driver.sleep(2)
            wait_element(driver, XPATHS["EMAIL_INPUT"], timeout=10).send_keys(EMAIL)
            wait_element(driver, XPATHS["PASSWORD_INPUT"], timeout=10).send_keys(PASSWORD)
            
            driver.sleep(2)
            CHECKBOX_COORDS = (675, 720)
            pyautogui.click(*CHECKBOX_COORDS)
            wait_element(driver, XPATHS["LOGIN_BUTTON"], timeout=10).click()
            return
        
        except:
            # print("Giriş başarısız, tekrar deneniyor...")
            time.sleep(delay)
            driver.refresh()
    raise Exception
        
# Selects a category from the dropdown menu
def select_category(driver, category_options, index, AWAY):

    AWAY = extract_match_details(driver)
    
    retry_count = 0
    max_retries = 3
    while retry_count < max_retries:
        try:
            wait_element(driver, XPATHS["CATEGORY_DROPDOWN"]).click()
            category_options = driver.find_elements(By.XPATH, XPATHS["CATEGORY_OPTIONS"])
            category_option = category_options[-1 if AWAY else index]
            category_name = category_option.text.split(" - ")[0]
            
            # Skip if the category is occupied
            if category_option.get_attribute("class") == "dropdown-option disabled" or "MİSAFİR" in category_name:
                # print(f"Kategori {category_name} ({index + 1}/{len(category_options)}) dolu")
                return None
            
            # print(f"\nKategori {category_name} ({index + 1}/{len(category_options)}) seçiliyor...")
            category_option.click()
            return category_name
        except Exception as error:
            # print(f"Kategori {index + 1} seçilemedi. Tekrar deneniyor ({retry_count + 1}/{max_retries})...\n{error}")
            retry_count += 1
            if retry_count == max_retries:
                # print(f"Kategori {index + 1} atlanıyor...\n")
                return None

# Selects a block from the dropdown menu
def select_block(driver, block_options, index):
    try:
        wait_options(driver, XPATHS["BLOCK_OPTIONS"])
        block_options = driver.find_elements(By.XPATH, XPATHS["BLOCK_OPTIONS"])

        block_option = block_options[index]
        if block_option == wait_element(driver, XPATHS["NULL_OPTION"]):
            return None
        driver.execute_script("arguments[0].scrollIntoView(true);", block_option)
        block_option.click()
        print(f"\nBlok {block_option.text}")
        return block_option.text
    except Exception as error:
        print(f"Bloklar sayılırken hata\n{error}")
        return None

# Count seats in the selected block
def count_block_seats(driver):
    try:
        # Click on the seat map button
        wait_element(driver, XPATHS["SEAT_MAP"]).click()

        # Handle the popup if it appears
        safe_click(driver, XPATHS["NO_SEATS_POPUP"])
        try:
            popup = wait_element(driver, XPATHS["NO_SEATS_POPUP"], timeout=5)
            if popup.is_displayed():
                # print("Pencere kapatılıyor...")
                popup.click()
                driver.execute_script("arguments[0].scrollIntoView(true);", wait_element(driver, XPATHS["SEAT_MAP"]))
                wait_element(driver, XPATHS["SEAT_MAP"]).click()
        except:
            # print("Popup görünmedi, koltuklar sayılıyor...")
            pass

        # Count total and occupied seats
        total = driver.find_elements(By.XPATH, XPATHS["ALL_SEATS"])
        occupied = driver.find_elements(By.XPATH, XPATHS["OCCUPIED_SEATS"])

        return len(total), len(occupied)

    except Exception as error:
        print(f"Koltuklar sayılırken hata: {error}")
        return 0, 0

# Main function to count seats
def count_seats(driver, AWAY):
    total_occupied, total_count = 0, 0

    # Dismiss cookie message if it appears
    safe_click(driver, XPATHS["COOKIE_MESSAGE"])

    # Click the dropdown menu and wait for category options
    wait_element(driver, XPATHS["CATEGORY_DROPDOWN"]).click()
    driver.sleep(2)
    wait_options(driver, XPATHS["CATEGORY_OPTIONS"])
    category_options = driver.find_elements(By.XPATH, XPATHS["CATEGORY_OPTIONS"])

    if AWAY:
        # Only select the last index for away matches
        index = len(category_options) - 1
        category_name = select_category(driver, category_options, index, AWAY)

        if category_name:
            # Category header
            category_header = "=" * 7 + "=" * len(category_name) + "=" * 7
            print(f"\n{category_header}\n====== {category_name} ======\n{category_header}")
            
            # Select a block from the dropdown menu
            wait_element(driver, XPATHS["BLOCK_DROPDOWN"]).click()
            wait_options(driver, XPATHS["BLOCK_OPTIONS"])
            block_options = driver.find_elements(By.XPATH, XPATHS["BLOCK_OPTIONS"])

            for j in range(len(block_options)):
                block_name = select_block(driver, block_options, j)
                if not block_name:
                    continue

                # Calculate seats
                total, occupied = count_block_seats(driver)
                total_count += total
                total_occupied += occupied
                
                block_occupancy = (occupied / total) * 100
                bar_length = int(block_occupancy / 6.25)
                occupancy_bar = "█" * bar_length + "░" * (16 - bar_length)
                print(f"{occupancy_bar} %{block_occupancy:.2f}\nSatılan bilet: {occupied} / {total} (Kalan: {total - occupied})")

                # Click 'Change seat'
                wait_element(driver, XPATHS["CHANGE_SEAT"]).click()
    else:
        for i in range(len(category_options)):
            category_name = select_category(driver, category_options, i, AWAY)
            
            if not category_name:
                continue

            # Category header
            category_header = "=" * 7 + "=" * len(category_name) + "=" * 7
            print(f"\n{category_header}\n====== {category_name} ======\n{category_header}")
            
            # Select a block from the dropdown menu
            wait_element(driver, XPATHS["BLOCK_DROPDOWN"]).click()
            wait_options(driver, XPATHS["BLOCK_OPTIONS"])
            block_options = driver.find_elements(By.XPATH, XPATHS["BLOCK_OPTIONS"])

            # Loop through all blocks
            for j in range(len(block_options)):
                block_name = select_block(driver, block_options, j)
                if not block_name:
                    continue

                # Calculate seats
                total, occupied = count_block_seats(driver)
                total_count += total
                total_occupied += occupied
                
                block_occupancy = (occupied / total) * 100
                bar_length = int(block_occupancy / 6.25)
                occupancy_bar = "█" * bar_length + "░" * (16 - bar_length)
                print(f"{occupancy_bar} %{block_occupancy:.2f}\nSatılan bilet: {occupied} / {total} (Kalan: {total - occupied})")

                # Click 'Change seat'
                wait_element(driver, XPATHS["CHANGE_SEAT"]).click()

            # Re-open category dropdown
            category_dropdown = wait_scroll(driver, XPATHS["CATEGORY_DROPDOWN"])
            driver.execute_script("arguments[0].click();", category_dropdown)
            wait_options(driver, XPATHS["CATEGORY_OPTIONS"])
            category_options = driver.find_elements(By.XPATH, XPATHS["CATEGORY_OPTIONS"])

    return total_count, total_occupied, category_options

def calculate_occupancy(driver, match_title, ticket, AWAY):
    global TOTAL_SEATS
    
    # Calculate all seats
    total_count, total_occupied, category_options = count_seats(driver, AWAY)
    total_available = total_count - total_occupied
    
    # Determine the total seat number
    if AWAY:
        TOTAL_SEATS = 154
    else:
        if len(category_options) >= 8:
            TOTAL_SEATS = 31827 
        elif len(category_options) <= 7:
            TOTAL_SEATS = 23770
        else:
            TOTAL_SEATS = 31827
    
    # Subtract a fixed number from total count since full blocks are not available on the website
    full_blocks = TOTAL_SEATS - total_count
    total_occupied += full_blocks
    
    # Calculate the occupancy rate and create an occupancy bar
    occupancy_rate = (total_occupied / TOTAL_SEATS) * 100
    bar_length = int(occupancy_rate / 6.25)
    occupancy_bar = "█" * bar_length + "░" * (16 - bar_length)
    
    # Final output
    output = f"{match_title}\n{occupancy_bar} %{occupancy_rate:.2f}\n{ticket}: {total_occupied:,} / {TOTAL_SEATS:,}"
    
    return output, occupancy_rate, total_available

def main():
    # Redirect all printed output to a text file
    with open("output.txt", "w", encoding="utf-8") as file:
        with redirect_stdout(file):
            with SB(uc=True, incognito=True) as driver:
                # Open the browser
                driver.maximize_window()
                driver.open(URL)
                try:
                    wait_element(driver, XPATHS["MATCH_TITLE"], timeout=30)
                except:
                    time.sleep(5)
                    driver.refresh()
                    wait_element(driver, XPATHS["MATCH_TITLE"], timeout=30)
                check_if_no_match(XPATHS["NO_MATCH"])
                
                # Extract match details
                match_details = extract_match_details(driver)
                if not match_details: 
                    return
                
                match_title, match_date, ticket, AWAY = match_details
                print(f"Veri tarihi: {current_date}\nNOT: Satışa açılan ve henüz dolmamış bloklar listelenmektedir.")
                print(f"\nMaç: {match_title}\nTarih: {match_date}")
        
                # Click on the match
                wait_element(driver, XPATHS["MATCH_URL"])
                driver.click(XPATHS["MATCH_URL"])
                    
                # Click on the buy button
                driver.sleep(2)
                wait_scroll(driver, XPATHS["BUY_BUTTON"])
                buy_button = wait_element(driver, XPATHS["BUY_BUTTON"])
                driver.execute_script("arguments[0].scrollIntoView(true);", buy_button)
                driver.execute_script("arguments[0].click();", buy_button)
                check_if_no_match(XPATHS["PRIORITY"])
                
                # Sign in passo.com.tr
                try:
                    login(driver)
                except:
                    time.sleep(5)
                    driver.refresh()
                    login(driver)
                    
                # Calculate the occupancy rate
                driver.execute_script("document.body.style.zoom='80%'")
                output, occupancy_rate, total_available = calculate_occupancy(driver, match_title, ticket, AWAY)
    
    # Add more info
    if occupancy_rate == 100:
        output += "\n🔥 KAPALI GİŞE"
    else:
        output += f" (Kalan: {total_available:,})"
        short_url = upload_to_gist()
        if short_url:
            output += f"\nKalan bloklar: {short_url}"
            
    return output, match_date

if __name__ == "__main__":
    print(main())
