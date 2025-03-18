import os
from dotenv import load_dotenv
from seleniumbase import SB
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pyautogui

load_dotenv(dotenv_path='../ks-tribun-doluluk/keys.env')
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

# XPaths
BUY_BTN_XPATH = "//button[text()= 'SATIN AL']"
LOGIN_BTN_XPATH = "//button[@class='black-btn']"
EMAIL_INPUT_XPATH = "//input[@placeholder='E-Posta Adresi']"
PASSWORD_INPUT_XPATH = "//input[@placeholder='Şifre']"
CATEGORY_DROPDOWN_XPATH = "//div[@id='blocks']"
CATEGORY_OPTIONS_XPATH = "//div[@class='dropdown-options']/div"
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

# Away seat info
AWAY_CATEGORY = "//span[contains(text(),'MİSAFİR')]"
AWAY_BLOCK = "//option[contains(text(),'GÜNEY')]"

# Match info
URL = "https://www.passo.com.tr/tr/ara?searchQuery=Kocaelispor&etkinlikdetayi=true"

AWAY = False
OPPONENT = "Sakaryaspor"

match = f"Kocaelispor - {OPPONENT}" if not AWAY else f"{OPPONENT} - Kocaelispor"
ticket = "Satılan bilet" if not AWAY else "Deplasman satılan bilet"

def wait_element(driver, xpath, timeout=60):
    return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))

def wait_options(driver, xpath, timeout=60):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))

def login(driver):
    wait_element(driver, EMAIL_INPUT_XPATH).send_keys(EMAIL)
    wait_element(driver, PASSWORD_INPUT_XPATH).send_keys(PASSWORD)
    driver.sleep(2)
    pyautogui.click(675, 720)
    driver.sleep(1)
    wait_element(driver, LOGIN_BTN_XPATH).click()

def count_seats(driver):
    total_occupied = 0
    total_count = 0
    try:
        cookie_button = driver.find_element(By.XPATH, "//a[@aria-label='dismiss cookie message']")
        cookie_button.click()
        driver.sleep(1)
    except Exception as e:
        print(f"Koltuklar sayılırken hata: {e}")

    # Click the dropdown menu and wait for category options
    wait_element(driver, CATEGORY_DROPDOWN_XPATH).click()
    driver.sleep(2)
    print("\nKategoriler yükleniyor...")
    wait_options(driver, CATEGORY_OPTIONS_XPATH)
    category_options = driver.find_elements(By.XPATH, CATEGORY_OPTIONS_XPATH)
    wait_element(driver, CATEGORY_DROPDOWN_XPATH).click()
    
    # Loop through categories
    for i in range(len(category_options)):
        try:
            if i >= len(category_options):
                break
            retry_count = 0
            max_retries = 3
            while retry_count < max_retries:
                try:
                    wait_element(driver, CATEGORY_DROPDOWN_XPATH).click()
                    driver.sleep(2)
                    wait_options(driver, CATEGORY_OPTIONS_XPATH)            
                    category_options = driver.find_elements(By.XPATH, CATEGORY_OPTIONS_XPATH)
                    
                    category_option = category_options[i]
                    driver.sleep(1)
                    category_text = category_option.text.split(" - ")[0]
                    print(f"\nKategori {category_text} ({i + 1}/{len(category_options)}) seçiliyor...")
                    category_option.click()
                    driver.sleep(1)
                    break
                except Exception as e:
                    print(f"Kategori {i + 1} seçilemedi. Tekrar deneniyor ({retry_count + 1}/{max_retries})...\n{e}")
                    retry_count += 1
                    if retry_count == max_retries:
                        print(f"Kategori {i + 1} atlanıyor...\n")
                        break 
            print(f"Seçili kategori: {category_text}")
                    
            # Click dropdown menu and wait for block options
            wait_element(driver, BLOCK_DROPDOWN_XPATH).click()
            driver.sleep(2)
            print("\nBloklar yükleniyor...")
            wait_options(driver, BLOCK_OPTIONS_XPATH)

            # Loop through blocks
            block_options = driver.find_elements(By.XPATH, BLOCK_OPTIONS_XPATH)
            for j in range(len(block_options)):
                try:
                    # driver.execute_script("window.scrollBy(0,350)")
                    wait_options(driver, BLOCK_OPTIONS_XPATH)
                    driver.sleep(1)
                    block_options = driver.find_elements(By.XPATH, BLOCK_OPTIONS_XPATH)
                    block_option = block_options[j]
                    if block_option == wait_element(driver, NULL_OPTION_XPATH):
                        continue
                    driver.execute_script("arguments[0].scrollIntoView(true);", block_option)
                    block_option.click()
                    print(f"Seçili blok: {block_option.text}")

                    # Open seat map
                    wait_element(driver, SEAT_MAP_XPATH).click()
                    print("\nKoltuklar sayılıyor...")
                    wait_element(driver, ALL_SEATS_XPATH)
                    try:
                        wait_element(driver, OCCUPIED_SEAT_XPATH)
                    except Exception:
                        print("Dolu koltuk bulunamadı, devam ediliyor...")

                    # Count seats
                    total = driver.find_elements(By.XPATH, ALL_SEATS_XPATH)
                    occupied = driver.find_elements(By.XPATH, OCCUPIED_SEAT_XPATH)

                    total_count += len(total)
                    total_occupied += len(occupied)
                    print(f"Blok {block_option.text}:\nToplam koltuk = {len(total)}\nDolu koltuk = {len(occupied)}\nDoluluk oranı = %{len(occupied) / len(total) * 100:.2f}")

                    # Change block
                    driver.sleep(2)
                    wait_element(driver, CHANGE_SEAT_XPATH).click()

                except Exception as error:
                    print(f"\nBlok dolu\n{error}")
                    continue
                
            wait_element(driver, CATEGORY_DROPDOWN_XPATH).click()
            driver.sleep(2)
            wait_options(driver, CATEGORY_OPTIONS_XPATH)
            category_options = driver.find_elements(By.XPATH, CATEGORY_OPTIONS_XPATH)

        except Exception as error:
            print(f"\nKategori dolu\n{error}")
            continue

    return total_count, total_occupied

def main():
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    chrome_options = Options()
    chrome_options.add_argument(f"user-agent={user_agent}")
    
    with SB(uc=True) as driver:
        # Open the browser
        driver.driver_options = chrome_options
        driver.maximize_window()
        driver.open(URL)
        # driver.sleep(2)
        
        # Find match
        match_title = driver.find_element(By.XPATH, MATCH_TITLE_XPATH)
        match_date = driver.find_element(By.XPATH, MATCH_DATE_XPATH)
        print(f"Maç: {match_title.text}\nTarih: {match_date.text}")
        wait_element(driver, MATCH_URL_XPATH)
        driver.click(MATCH_URL_XPATH)
        
        # Press the buy button
        driver.sleep(2)
        driver.execute_script("window.scrollBy(0,550)")
        wait_element(driver, BUY_BTN_XPATH).click()
        driver.sleep(2)
        
        # Login
        login(driver)
        # Count all seats
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
        
        output = f"{match}\n{occupancy_bar} %{occupancy_rate:.2f}\n{ticket}: {total_occupied:,} / {HOME_TOTAL:,}"
        if occupancy_rate == 100:
            output += "\n🔥 KAPALI GİŞE"
        else:
            output += f" (Kalan: {total_available:,})"
            
    return output

if __name__ == "__main__":
    print(main())
