from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
import time

STREAMLIT_URLS = [
    "https://school-career-guidance-app.streamlit.app/",
    "https://insighted-mvp.streamlit.app/",
    "https://cv4ctapp.streamlit.app/",
    "https://mineralgroupclassification.streamlit.app/",
]

def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

def wake_up_app(driver, url):
    print(f"\n🔗 Opening: {url}")
    driver.get(url)

    wait = WebDriverWait(driver, 15)

    try:
        button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(),'Yes, get this app back up')]")
            )
        )
        print("😴 App is sleeping. Clicking wake-up button...")
        button.click()

        try:
            wait.until(
                EC.invisibility_of_element_located(
                    (By.XPATH, "//button[contains(text(),'Yes, get this app back up')]")
                )
            )
            print("✅ App successfully woken up")
        except TimeoutException:
            print("⚠️ Button clicked but did not disappear")

    except TimeoutException:
        print("✅ App already awake (no wake-up button found)")

def main():
    driver = create_driver()

    try:
        for url in STREAMLIT_URLS:
            wake_up_app(driver, url)
            time.sleep(5)  # небольшая пауза между приложениями
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        exit(1)
    finally:
        driver.quit()
        print("\n🚀 All done. Script finished.")

if __name__ == "__main__":
    main()
