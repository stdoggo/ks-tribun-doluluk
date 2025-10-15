import os
import csv
import time
import pytz
import locale
import requests
import pyautogui
from datetime import datetime
from dotenv import load_dotenv
from functools import lru_cache
from contextlib import redirect_stdout
from seleniumbase import SB
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from requests.exceptions import RequestException

# Login credentials
load_dotenv(dotenv_path='keys.env')

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Date of the data
timezone = pytz.timezone("Europe/Istanbul")
current_date = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")

# URL
URL = "https://www.passo.com.tr/tr/kombine/kocaelispor-2025-2026-kombine-mac-biletleri/567746"

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
    "MATCH_TITLE": "//div[@class='r-title' and contains(text(), 'Kocaelispor')]",
    "MATCH_DATE": "//span[@class='r-date']",
    "MATCH_TIME": "//span[@class='r-date']/div",
    "MATCH_URL": f"//div[contains(text(),'Kocaelispor')]",
    "NO_SEATS_POPUP": "//button[contains(text(),'Tamam')]",
    "COOKIE_MESSAGE": "//a[@aria-label='dismiss cookie message']",
    "PRIORITY": "//div[contains(text(),'Kongre')]"
}
    
def wait_element(driver, xpath, timeout=60):
    element = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
    return element

def click_element(driver, xpath, timeout=60):
    element = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
    if not element.is_displayed():
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
    driver.execute_script("arguments[0].click();", element)
    return element

# Click element with the try-except block
def safe_click(driver, xpath):
    try:
        click_element(driver, xpath)
    except Exception:
        pass

# Shorten github URL
def shorten_url(long_url):
    try:
        response = requests.get(f"http://tinyurl.com/api-create.php?url={long_url}", timeout=10)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        return None

# Upload output.txt to Github
def upload_to_gist():
    filename = "output.txt"
    description = f"Blok doluluk durumu ({current_date})"
    public = True

    try:
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

        response = requests.post(
            "https://api.github.com/gists",
            json=payload,
            headers={
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json"
            },
            timeout=15
        )

        if response.status_code == 201:
            gist_data = response.json()
            raw_url = list(gist_data["files"].values())[0]["raw_url"]
            return shorten_url(raw_url)
        return None
    except (RequestException, OSError):
        return None
    
# Sign in passo.com.tr
def login(driver, attempts=5, delay=20):
    for i in range(attempts):
        try:
            driver.sleep(2)
            wait_element(driver, XPATHS["EMAIL_INPUT"], timeout=10).send_keys(EMAIL)
            wait_element(driver, XPATHS["PASSWORD_INPUT"], timeout=10).send_keys(PASSWORD)
            
            driver.sleep(2)
            CHECKBOX_COORDS = (670, 730)
            pyautogui.click(*CHECKBOX_COORDS)
            click_element(driver, XPATHS["LOGIN_BUTTON"], timeout=10)
            return
        
        except:
            # print("Giriş başarısız, tekrar deneniyor...")
            time.sleep(delay)
            driver.refresh()
    raise Exception
        
# Selects a category from the dropdown menu
def select_category(driver, category_options, index):
    
    retry_count = 0
    max_retries = 3
    while retry_count < max_retries:
        try:
            click_element(driver, XPATHS["CATEGORY_DROPDOWN"])
            category_options = driver.find_elements(By.XPATH, XPATHS["CATEGORY_OPTIONS"])
            category_option = category_options[index]
            category_name = category_option.text.split(" - ")[0]
            
            # Skip if the category is occupied
            is_occupied = category_option.get_attribute("class") == "dropdown-option disabled" or "MİSAFİR" in category_name
            if is_occupied:
                return None
            
            driver.execute_script("arguments[0].scrollIntoView(true);", category_option)
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
        click_element(driver, XPATHS["BLOCK_OPTIONS"])
        block_options = driver.find_elements(By.XPATH, XPATHS["BLOCK_OPTIONS"])
        block_option = block_options[index]
        
        if block_option == wait_element(driver, XPATHS["NULL_OPTION"]):
            return None
        
        driver.execute_script("arguments[0].scrollIntoView(true);", block_option)
        block_option.click()
        print(f"\nBlok: {block_option.text}")
        return block_option.text
    except Exception as error:
        # print(f"Bloklar sayılırken hata\n{error}")
        return None

# Count seats in the selected block
def count_block_seats(driver):
    try:
        # Click on the seat map button
        click_element(driver, XPATHS["SEAT_MAP"])

        # Handle the popup if it appears
        safe_click(driver, XPATHS["NO_SEATS_POPUP"])
        try:
            popup = wait_element(driver, XPATHS["NO_SEATS_POPUP"], timeout=5)
            if popup.is_displayed():
                popup.click()
                click_element(driver, XPATHS["SEAT_MAP"])
        except:
            pass

        # Count total and occupied seats
        total = driver.find_elements(By.XPATH, XPATHS["ALL_SEATS"])
        occupied = driver.find_elements(By.XPATH, XPATHS["OCCUPIED_SEATS"])

        return len(total), len(occupied)

    except Exception as error:
        # print(f"Koltuklar sayılırken hata: {error}")
        return 0, 0

# Process block statistics
def process_block(driver, block_name, total_count, total_occupied, category_count=0, category_occupied=0):
    
    # Calculate seats
    total, occupied = count_block_seats(driver)
    total_count += total
    total_occupied += occupied
    
    category_count += total
    category_occupied += occupied
    
    if total > 0:
        block_occupancy = (occupied / total) * 100
        bar_length = int(block_occupancy / 6.25)
        occupancy_bar = "█" * bar_length + "░" * (16 - bar_length)
        print(f"{occupancy_bar} %{block_occupancy:.2f}\nSatılan kombine: {occupied} / {total} (Kalan: {total - occupied})")

    # Click 'Change seat'
    click_element(driver, XPATHS["CHANGE_SEAT"])
    
    return total_count, total_occupied, category_count, category_occupied

# Extract category capacities
def extract_categories(filename="categories.csv"):
    try:
        categories = []
        category_capacity = []
        with open(filename, "r", encoding="utf-8") as file:
            reader = csv.reader(file, delimiter=';')
            for row in reader:
                if len(row) >= 2:
                    categories.append(row[0].strip())
                    category_capacity.append(row[1].strip())
        return categories, category_capacity
    except OSError as error:
        print(f"Dosya okunamadı\n{error}")
        return [], []

# Process category and its blocks
def process_category(driver, category_name, total_count, total_occupied):
    # Initialize category counters
    category_count, category_occupied = 0, 0
    
    # Get category capacity based on home/away game
    categories, capacities = extract_categories()
    try:
        category_capacity = int(next((cap for cat, cap in zip(categories, capacities) if cat == category_name), 0))
    except ValueError:
        category_capacity = 0
        
    # Category header
    category_header = "=" * 7 + "=" * len(category_name) + "=" * 7
    print(f"\n{category_header}\n====== {category_name} ======\n{category_header}")
    
    # Select a block from the dropdown menu
    wait_element(driver, XPATHS["BLOCK_DROPDOWN"]).click()
    wait_element(driver, XPATHS["BLOCK_OPTIONS"])
    block_options = driver.find_elements(By.XPATH, XPATHS["BLOCK_OPTIONS"])

    # Loop through all blocks
    for j in range(len(block_options)):
        block_name = select_block(driver, block_options, j)
        if not block_name:
            continue

        total_count, total_occupied, category_count, category_occupied = process_block(driver, block_name, total_count, total_occupied, category_count, category_occupied)
        
    category_full_blocks = category_capacity - category_count
    category_occupied += category_full_blocks
    category_occupancy = (category_occupied / category_capacity) * 100
    bar_length = int(category_occupancy / 6.25)
    occupancy_bar = "█" * bar_length + "░" * (16 - bar_length)
    
    print("-" * 7 + "-" * len(category_name) + "-" * 7)
    print(f"Kategori: {category_name}\n{occupancy_bar} %{category_occupancy:.2f}\nSatılan kombine: {category_occupied} / {category_capacity} (Kalan: {category_capacity - category_occupied})")
    
    category_count, category_occupied = 0, 0
    
    return total_count, total_occupied

# Main function to count seats
def count_seats(driver):
    total_occupied, total_count = 0, 0

    # Dismiss cookie message if it appears
    safe_click(driver, XPATHS["COOKIE_MESSAGE"])

    # Click the dropdown menu and wait for category options
    click_element(driver, XPATHS["CATEGORY_DROPDOWN"])
    driver.sleep(1)  # Add small delay
    category_options = driver.find_elements(By.XPATH, XPATHS["CATEGORY_OPTIONS"])
    num_categories = len(category_options)

    for i in range(num_categories):
        # Re-open category dropdown for each iteration
        if i > 0:
            click_element(driver, XPATHS["CATEGORY_DROPDOWN"])
            driver.sleep(1)  # Add small delay
            category_options = driver.find_elements(By.XPATH, XPATHS["CATEGORY_OPTIONS"])
            
        category_name = select_category(driver, category_options, i)
        
        if not category_name:
            continue

        total_count, total_occupied = process_category(driver, category_name, total_count, total_occupied)

    return total_count, total_occupied, category_options

def calculate_occupancy(driver):
    # Calculate all seats
    total_count, total_occupied, _ = count_seats(driver)
    total_available = total_count - total_occupied
    
    # Determine the total seat number
    TOTAL_SEATS = 31827
    
    # Subtract a fixed number from total count since full blocks are not available on the website
    full_blocks = TOTAL_SEATS - total_count
    total_occupied += full_blocks
    
    # Calculate the occupancy rate and create an occupancy bar
    occupancy_rate = (total_occupied / TOTAL_SEATS) * 100 if TOTAL_SEATS > 0 else 0
    bar_length = int(occupancy_rate / 6.25)
    occupancy_bar = "█" * bar_length + "░" * (16 - bar_length)
    
    # Final output
    output = f"Kocaelispor 2025/26 kombine \n{occupancy_bar} %{occupancy_rate:.2f}\nKombine satışı: {total_occupied:,} / {TOTAL_SEATS:,}"
    
    return output, occupancy_rate, total_available

def main():
    # Redirect all printed output to a text file
    with open("output.txt", "w", encoding="utf-8") as file:
        with redirect_stdout(file):
            with SB(uc=True, incognito=True) as driver:
                # Open the browser
                driver.maximize_window()
                driver.open(URL)
                
                print(f"Veri tarihi: {current_date}")
                    
                # Click on the buy button
                driver.sleep(2)
                click_element(driver, XPATHS["BUY_BUTTON"])
                
                # Sign in passo.com.tr
                try:
                    login(driver)
                except:
                    time.sleep(5)
                    driver.refresh()
                    login(driver)
                    
                #if wait_element(driver, XPATHS["PRIORITY"], timeout=10).is_displayed():
                #    return "Biletler henüz genel satışa açılmadı."     
                #else:
                #    pass 

                # Calculate the occupancy rate
                driver.execute_script("document.body.style.zoom='70%'")
                output, occupancy_rate, total_available = calculate_occupancy(driver)
    
    # Add more info
    if occupancy_rate == 100:
        output += "\n🔥 KAPALI GİŞE"
    else:
        output += f" (Kalan: {total_available:,})"
        short_url = upload_to_gist()
        if short_url:
            output += f"\nKalan bloklar: {short_url}\n\n*Bazı koltuklar güvenlik, delegasyon vb. gerekçelerden dolayı satışa açılmayıp, dolu koltuk olarak gözükmektedir."
            
    return output

if __name__ == "__main__":
    print(main())
    # main()