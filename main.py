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
URL = "https://www.passo.com.tr/tr/ara?searchQuery=Kocaelispor&etkinlikdetayi=false"

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
    "MATCH_TITLE": "(//div[@class='r-title' and contains(text(), 'Kocaelispor')])[1]",
    "MATCH_DATE": "(//span[@class='r-date'])[1]",
    "MATCH_TIME": "//span[@class='r-date']/div[1]",
    "MATCH_URL": "(//div[contains(text(),'Kocaelispor')])[1]",
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

# Extract opponent name
@lru_cache(maxsize=1)
def extract_clubs(filename="club_list.csv"):
    try:
        clubs = []
        capacities = []
        with open(filename, "r", encoding="utf-8") as file:
            reader = csv.reader(file, delimiter=';')
            for row in reader:
                if len(row) >= 2:
                    clubs.append(row[0].strip())
                    capacities.append(row[1].strip())
        return clubs, capacities
    except OSError as error:
        print(f"Dosya okunamadı\n{error}")
        return [], []

def extract_match_details(driver):
    try:
        # Find match and extract the opponent details
        clubs, capacity = extract_clubs()
        match_text = wait_element(driver, XPATHS["MATCH_TITLE"]).text
        opponent = next((club for club in clubs if club in match_text), "Takım bulunamadı")
        opponent_capacity = int(next((capacity[i].replace(".", "").replace(",", "") for i, club in enumerate(clubs) if club == opponent), "0"))
        
        if "Spor" in opponent:
            opponent = opponent.replace("Spor", "spor").replace(" ", "")

        # Find out if it's home or away game
        AWAY = match_text.split(" - ")[0].strip() != "Kocaelispor"

        # Extract match details
        locale.setlocale(locale.LC_TIME, "tr_TR.UTF-8")
        match_date = wait_element(driver, XPATHS["MATCH_DATE"]).text.replace("\n", " ")

        match_title = f"Kocaelispor - {opponent}" if not AWAY else f"{opponent} - Kocaelispor"
        ticket = "Satılan bilet" if not AWAY else "Deplasman satılan bilet"

        return match_title, match_date, ticket, AWAY, opponent_capacity
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
            click_element(driver, XPATHS["LOGIN_BUTTON"], timeout=10)
            return
        
        except:
            # print("Giriş başarısız, tekrar deneniyor...")
            time.sleep(delay)
            driver.refresh()
    raise Exception
        
# Selects a category from the dropdown menu
def select_category(driver, category_options, index, AWAY):
    retry_count = 0
    max_retries = 3
    while retry_count < max_retries:
        try:
            # Click dropdown and wait for options to be visible
            click_element(driver, XPATHS["CATEGORY_DROPDOWN"])
            driver.sleep(1)
            
            # Get list of options
            category_options = driver.find_elements(By.XPATH, XPATHS["CATEGORY_OPTIONS"])
            if not category_options:
                retry_count += 1
                continue
                
            category_option = category_options[-1 if AWAY else index]
            category_name = category_option.text.split(" - ")[0]
            
            # Skip if the category is occupied
            is_occupied = "disabled" in category_option.get_attribute("class")
            if is_occupied:
                return None
            
            driver.execute_script("arguments[0].scrollIntoView(true);", category_option)
            driver.sleep(0.5) 
            category_option.click()
            
            # Verify selection was successful by checking if dropdown is closed
            driver.sleep(1) 
            dropdown = driver.find_elements(By.XPATH, XPATHS["CATEGORY_OPTIONS"])
            if not dropdown or not dropdown[0].is_displayed():
                return category_name
            
            retry_count += 1
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
def process_block(driver, block_name, total_count, total_occupied):
    # Calculate seats
    total, occupied = count_block_seats(driver)
    total_count += total
    total_occupied += occupied
    
    if total > 0:
        block_occupancy = (occupied / total) * 100
        bar_length = int(block_occupancy / 6.25)
        occupancy_bar = "█" * bar_length + "░" * (16 - bar_length)
        print(f"{occupancy_bar} %{block_occupancy:.2f}\nSatılan bilet: {occupied} / {total} (Kalan: {total - occupied})")

    # Click 'Change seat'
    click_element(driver, XPATHS["CHANGE_SEAT"])
    
    return total_count, total_occupied

# Process category and its blocks
def process_category(driver, category_name, total_count, total_occupied):
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

        total_count, total_occupied = process_block(driver, block_name, total_count, total_occupied)
    
    return total_count, total_occupied

# Main function to count seats
def count_seats(driver, AWAY):
    total_occupied, total_count = 0, 0

    # Dismiss cookie message if it appears
    safe_click(driver, XPATHS["COOKIE_MESSAGE"])

    # Click the dropdown menu and wait for category options
    click_element(driver, XPATHS["CATEGORY_DROPDOWN"])
    # wait_element(driver, XPATHS["CATEGORY_OPTIONS"])
    category_options = driver.find_elements(By.XPATH, XPATHS["CATEGORY_OPTIONS"])

    if AWAY:
        # Only select the last index for away matches
        index = len(category_options) - 1
        category_name = select_category(driver, category_options, index, AWAY)

        if category_name:
            total_count, total_occupied = process_category(driver, category_name, total_count, total_occupied)
    else:
        for i in range(len(category_options) - 1):
            category_name = select_category(driver, category_options, i, AWAY)
            
            if not category_name:
                continue

            total_count, total_occupied = process_category(driver, category_name, total_count, total_occupied)

            # Re-open category dropdown
            click_element(driver, XPATHS["CATEGORY_DROPDOWN"])
            wait_element(driver, XPATHS["CATEGORY_OPTIONS"])
            category_options = driver.find_elements(By.XPATH, XPATHS["CATEGORY_OPTIONS"])

    return total_count, total_occupied, category_options

def calculate_occupancy(driver, match_title, ticket, AWAY, opponent_capacity):
    # Calculate all seats
    total_count, total_occupied, category_options = count_seats(driver, AWAY)
    total_available = total_count - total_occupied
    
    # Determine the total seat number
    if AWAY:
        TOTAL_SEATS = opponent_capacity
    else:
        TOTAL_SEATS = 27963
    
    # Subtract a fixed number from total count since full blocks are not available on the website
    full_blocks = TOTAL_SEATS - total_count
    total_occupied += full_blocks
    
    # Calculate the occupancy rate and create an occupancy bar
    occupancy_rate = (total_occupied / TOTAL_SEATS) * 100 if TOTAL_SEATS > 0 else 0
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
                    
                # Check if there are any matches available
                try:
                    element = wait_element(driver, XPATHS["MATCH_TITLE"], timeout=10)
                    if not element.is_displayed():
                        return "Maç bulunamadı."
                except:
                    return "Maç bulunamadı."
                
                # Extract match details
                match_details = extract_match_details(driver)
                if not match_details:
                    return "Maç detayları alınamadı."
                match_title, match_date, ticket, AWAY, opponent_capacity = match_details
                print(f"Veri tarihi: {current_date}\nNOT: Satışa açılan ve henüz dolmamış bloklar listelenmektedir.")
                print(f"\nMaç: {match_title}\nTarih: {match_date}")
        
                # Click on the match
                wait_element(driver, XPATHS["MATCH_URL"])
                driver.click(XPATHS["MATCH_URL"])
                    
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
                output, occupancy_rate, total_available = calculate_occupancy(driver, match_title, ticket, AWAY, opponent_capacity)
    
    # Add more info
    if occupancy_rate == 100:
        output += "\n🔥 KAPALI GİŞE"
    else:
        output += f" (Kalan: {total_available:,})"
        short_url = upload_to_gist()
        if short_url:
            output += f"\nKalan bloklar: {short_url}"
            
    return output

if __name__ == "__main__":
    print(main())
    # main()