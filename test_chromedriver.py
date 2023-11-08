from selenium import webdriver
from selenium.webdriver.chrome.service import Service

# Use to test downloading your updated chromedriver for selenium
# Set up ChromeDriver path
CHROME_DRIVER_PATH = "/usr/local/bin/chromedriver"  # Replace with your path

# Initialize WebDriver

s = Service(CHROME_DRIVER_PATH)
driver = webdriver.Chrome(service=s)


# Navigate to a website
driver.get('https://www.google.com')

# Close the browser
driver.quit()
