"""連到 Selenium Grid (docker-selenium) 的最小範例.

啟動 grid:
    docker compose -f docker-compose-standalone-chrome.yml up
    # 或 firefox / edge / hub-and-nodes

執行:
    pip install selenium
    python demo.py
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Selenium 4 之後 endpoint 直接用根路徑就行 (/wd/hub 仍可用以相容舊程式)
GRID_URL = "http://localhost:4444"

# options = webdriver.ChromeOptions()
options = webdriver.FirefoxOptions()
# options = webdriver.EdgeOptions()

# 想跑 headless 把下面打開 (Chrome v132+ 一律走 --headless=new, 容器內仍建議保留 Xvfb)
# options.add_argument("--headless=new")

# 加 metadata, 配合 SE_VIDEO_FILE_NAME=auto 可以讓錄影檔名帶上測試名稱
options.set_capability("se:name", "demo-google-search")

browser = webdriver.Remote(command_executor=GRID_URL, options=options)
try:
    browser.get("https://www.google.com")
    print("title:", browser.title)

    # 比 sleep 穩很多 - 等元素出現再操作
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.NAME, "q"))
    )

    browser.save_screenshot("screenshot.png")
finally:
    browser.quit()
