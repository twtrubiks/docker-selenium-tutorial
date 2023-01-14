from selenium import webdriver

browser = webdriver.Remote(
    command_executor='http://localhost:4444/wd/hub',
    # options=webdriver.ChromeOptions()
    options=webdriver.FirefoxOptions()
)

browser.get('https://www.google.com')
print(browser.title)
browser.save_screenshot("firefox.png")
browser.quit()