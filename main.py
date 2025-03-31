import os
import sys
import pytz
import requests
import pyautogui
from dotenv import load_dotenv
from datetime import datetime
from seleniumbase import SB
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# Date of the data
timezone = pytz.timezone("Europe/Istanbul")
current_date = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")

# Login credentials
load_dotenv(dotenv_path='../ks-tribun-doluluk/keys.env')

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
github_token = os.getenv("GITHUB_TOKEN")

# XPaths
BUY_BTN_XPATH = "//button[text()= 'SATIN AL']"
LOGIN_BTN_XPATH = "//button[@class='black-btn']"
EMAIL_INPUT_XPATH = "//input[@placeholder='E-Posta Adresi']"
PASSWORD_INPUT_XPATH = "//input[@placeholder='Şifre']"
CATEGORY_DROPDOWN_XPATH = "//div[@id='blocks']"
CATEGORY_OPTIONS_XPATH = "//div[@class='dropdown-options']/div"
DISABLED_OPTION_XPATH = "//div[@class='dropdown-options']/div[@class='dropdown-option disabled']"
BLOCK_DROPDOWN_XPATH = "//select[@id='blocks']"
BLOCK_OPTIONS_XPATH = "//select[@id='blocks']/option"
NULL_OPTION_XPATH = "//select[@id='blocks']/option[contains(text(),'Blok Seçiniz')]"
SEAT_MAP_XPATH = "//button[@id='custom_seat_button']"
ALL_SEATS_XPATH = "//*[@class='seats']/*[@class='seat']"
OCCUPIED_SEAT_XPATH = "//*[@class='seats']/*[@class='seat']/*[@fill='#7691a7']"
AVAILABLE_SEAT_XPATH = "//*[@fill='#ffffff']"
CHANGE_SEAT_XPATH = "//button[contains(text(),'Seçimi değiştir')]"
MATCH_TITLE_XPATH = "//div[@class='r-title']"
MATCH_DATE_XPATH = "//span[@class='r-date']"
MATCH_TIME_XPATH = "//span[@class='r-date']/div"
MATCH_URL_XPATH = "//div[@class='wrapper row event-search-items']/div[1]/div/div/div[2]"
NO_SEATS_POPUP_XPATH = "//button[contains(text(),'Tamam')]"

# Away seat info
AWAY_CATEGORY = "//span[contains(text(),'MİSAFİR')]"
AWAY_BLOCK = "//option[contains(text(),'GÜNEY')]"

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
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github+json"
            }
        )

        if response.status_code == 201:  # HTTP 201 Created
            gist_data = response.json()
            raw_url = list(gist_data["files"].values())[0]["raw_url"]
            short_url = shorten_url(raw_url)
            return short_url
        else:
            print(f"Hata kodu: {response.status_code}")
            print(f"{response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Hata: {e}")
        return None

# Extract opponent name
def extract_clubs(filename="club_list.txt"):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return [line.strip() for line in file.readlines()]
    except OSError as error:
        print(f"Dosya okunamadı\n{error}")
        
clubs = extract_clubs()

def extract_match_details(driver, clubs):
    # Find match and extract the opponent details
    match_title = driver.find_element(By.XPATH, MATCH_TITLE_XPATH).text
    opponent = next((club for club in clubs if club in match_title), "Takım bulunamadı")
    
    # Find out if it's home or away game
    AWAY = match_title.split(" - ")[0].strip() != "Kocaelispor"
    
    # Extract match details
    match_date = driver.find_element(By.XPATH, MATCH_DATE_XPATH).text
    match_day, match_time = match_date.split("\n")
    
    match = f"Kocaelispor - {opponent}" if not AWAY else f"{opponent} - Kocaelispor"
    ticket = "Satılan bilet" if not AWAY else "Deplasman satılan bilet"
    
    return match, match_day, match_time, ticket

# Wait for the element to load
def wait_element(driver, xpath, timeout=60):
    return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))

# Wait for dropdown menu options to load
def wait_options(driver, xpath, timeout=60):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))

# Sign in passo.com.tr
def login(driver):
    driver.sleep(2)
    wait_element(driver, EMAIL_INPUT_XPATH).send_keys(EMAIL)
    wait_element(driver, PASSWORD_INPUT_XPATH).send_keys(PASSWORD)
    driver.sleep(2)
    CHECKBOX_COORDS = (675, 720)
    pyautogui.click(*CHECKBOX_COORDS)
    wait_element(driver, LOGIN_BTN_XPATH).click()

# Dismiss cookie message if it appaers
def dismiss_cookie_message(driver):
    try:
        wait_element(driver, "//a[@aria-label='dismiss cookie message']").click()
    except Exception as e:
        pass

# Selects a category from the dropdown menu
def select_category(driver, category_options, index):
    
    retry_count = 0
    max_retries = 3
    while retry_count < max_retries:
        try:
            wait_element(driver, CATEGORY_DROPDOWN_XPATH).click()
            # wait_options(driver, CATEGORY_OPTIONS_XPATH)
            category_options = driver.find_elements(By.XPATH, CATEGORY_OPTIONS_XPATH)

            category_option = category_options[index]
            category_name = category_option.text.split(" - ")[0]
            
            # Skip if the category is occupied
            if category_option.get_attribute("class") == "dropdown-option disabled":
                # print(f"Kategori {category_name} ({index + 1}/{len(category_options)}) dolu")
                return None
            
            # print(f"\nKategori {category_name} ({index + 1}/{len(category_options)}) seçiliyor...")
            category_option.click()
            return category_name
        except Exception as e:
            # print(f"Kategori {index + 1} seçilemedi. Tekrar deneniyor ({retry_count + 1}/{max_retries})...\n{e}")
            retry_count += 1
            if retry_count == max_retries:
                # print(f"Kategori {index + 1} atlanıyor...\n")
                return None

# Selects a block from the dropdown menu
def select_block(driver, block_options, index):
    try:
        wait_options(driver, BLOCK_OPTIONS_XPATH)
        block_options = driver.find_elements(By.XPATH, BLOCK_OPTIONS_XPATH)

        block_option = block_options[index]
        if block_option == wait_element(driver, NULL_OPTION_XPATH):
            return None
        driver.execute_script("arguments[0].scrollIntoView(true);", block_option)
        block_option.click()
        print(f"\nBlok {block_option.text}")
        return block_option.text
    except Exception as e:
        print(f"Bloklar sayılırken hata\n{e}")
        return None

# Count seats in the selected block
def count_block_seats(driver):
    try:
        wait_element(driver, SEAT_MAP_XPATH).click()

        # Close popup if it appears
        try:
            wait_element(driver, NO_SEATS_POPUP_XPATH).click()
        except Exception:
            pass

        # print("Koltuklar sayılıyor...")
        wait_element(driver, ALL_SEATS_XPATH)
        total = driver.find_elements(By.XPATH, ALL_SEATS_XPATH)
        occupied = driver.find_elements(By.XPATH, OCCUPIED_SEAT_XPATH)

        return len(total), len(occupied)
    except Exception as e:
        print(f"Koltuklar sayılırken hata\n{e}")
        return 0, 0

# Main function to count seats
def count_seats(driver):
    total_occupied, total_count = 0, 0

    dismiss_cookie_message(driver)

    # Click the dropdown menu and wait for category options
    wait_element(driver, CATEGORY_DROPDOWN_XPATH).click()
    driver.sleep(2)
    # print("\nKategoriler yükleniyor...")
    wait_options(driver, CATEGORY_OPTIONS_XPATH)
    category_options = driver.find_elements(By.XPATH, CATEGORY_OPTIONS_XPATH)
    wait_element(driver, CATEGORY_DROPDOWN_XPATH).click()

    for i in range(len(category_options)):
        try:
            if i >= len(category_options):
                break

            category_name = select_category(driver, category_options, i)
            if not category_name:
                continue
            print(f"\n==========================================\n====== {category_name} ======\n==========================================")

            # Open dropdown menu and wait for block options
            wait_element(driver, BLOCK_DROPDOWN_XPATH).click()
            # print("Bloklar yükleniyor...")
            wait_options(driver, BLOCK_OPTIONS_XPATH)
            block_options = driver.find_elements(By.XPATH, BLOCK_OPTIONS_XPATH)
            
            for j in range(len(block_options)):
                block_name = select_block(driver, block_options, j)
                if not block_name:
                    continue

                total, occupied = count_block_seats(driver)
                total_count += total
                total_occupied += occupied
                
                block_occupancy = (occupied / total) * 100
                bar_length = int(block_occupancy / 6.25)
                occupancy_bar = "█" * bar_length + "░" * (16 - bar_length)

                print(f"{occupancy_bar} %{block_occupancy:.2f}\nSatılan bilet: {occupied} / {total} (Kalan: {total - occupied})")

                # Change block
                wait_element(driver, CHANGE_SEAT_XPATH).click()

            # Re-select category dropdown menu
            wait_element(driver, CATEGORY_DROPDOWN_XPATH).click()
            wait_options(driver, CATEGORY_OPTIONS_XPATH)
            category_options = driver.find_elements(By.XPATH, CATEGORY_OPTIONS_XPATH)

        except Exception:
            # print(f"\nKategorideki tüm bloklar sayıldı\n")
            continue

    return total_count, total_occupied

def main():
    # Passo URL
    URL = "https://www.passo.com.tr/tr/ara?searchQuery=Kocaelispor&etkinlikdetayi=true"
    
    # Redirect all printed output to a text file
    with open("output.txt", "w", encoding="utf-8") as file:
        sys.stdout = file

        # user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        # chrome_options = Options()
        # chrome_options.add_argument(f"user-agent={user_agent}")
        
        with SB(uc=True) as driver:
            # Open the browser
            # driver.driver_options = chrome_options
            driver.maximize_window()
            driver.open(URL)

            # Extract match details
            match, match_day, match_time, ticket = extract_match_details(driver, clubs)
            print(f"Veri tarihi: {current_date}\nNOT: Satışa açılan ve henüz dolmamış bloklar listelenmektedir.")
            print(f"\nMaç: {match}\nTarih: {match_day}, {match_time}")
    
            # Click on the match
            wait_element(driver, MATCH_URL_XPATH)
            driver.click(MATCH_URL_XPATH)
            
            # Click on the buy button
            driver.sleep(2)
            driver.execute_script("window.scrollBy(0,550)")
            wait_element(driver, BUY_BTN_XPATH).click()
            
            # Sign in passo.com.tr
            login(driver)
            
            # Calculate all seats
            total_count, total_occupied = count_seats(driver)
            
            # Calculate and print the results
            HOME_TOTAL = 31827 + 1775
            total_available = total_count - total_occupied
            full_blocks = HOME_TOTAL - total_count
            total_occupied += full_blocks
            occupancy_rate = (total_occupied / HOME_TOTAL) * 100
            
            bar_length = int(occupancy_rate / 6.25)
            occupancy_bar = "█" * bar_length + "░" * (16 - bar_length)
            
            output = f"\n{match}\n{occupancy_bar} %{occupancy_rate:.2f}\n{ticket}: {total_occupied:,} / {HOME_TOTAL:,}"
                    
    # Return stdout to its original state
    sys.stdout = sys.__stdout__
    
    # Add more info
    if occupancy_rate == 100:
        output += "\n🔥 KAPALI GİŞE"
    else:
        output += f" (Kalan: {total_available:,})"
        short_url = upload_to_gist()
        if short_url:
            output += f"\nBloklar: {short_url}"
    return output 

if __name__ == "__main__":
    print(main())
