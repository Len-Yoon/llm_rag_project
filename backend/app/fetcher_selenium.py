# backend/app/fetcher_selenium.py
import contextlib, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class SimpleFetcher:
    def __init__(self, headless: bool = True):
        opts = Options()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--window-size=1280,2400")
        opts.add_argument("--lang=ko-KR")
        opts.page_load_strategy = "eager"
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=opts)

    def get_text(self, url: str) -> str:
        self.driver.get(url)
        try:
            WebDriverWait(self.driver, 7).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except Exception:
            pass
        time.sleep(0.5)
        try:
            return self.driver.find_element(By.TAG_NAME, "body").text.strip()
        except Exception:
            return ""

    def close(self):
        with contextlib.suppress(Exception):
            self.driver.quit()
