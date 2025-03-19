
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os

# Path to chromedriver
chromedriver_path = "" # REPLACE WITH THE PATH TO YOUR DOWNLOADED CHROMEDRIVER

# Your Web of Science login credentials (REPLACE)
username = ""
password = ""

# Setup WebDriver
service = Service(chromedriver_path)
driver = webdriver.Chrome(service=service)

# Open the login page directly
driver.get("https://access.clarivate.com/login?app=wos&locale=en-US")

# Wait for the login page to load
time.sleep(5)

# Find the email input field by ID and enter your username
email_field = driver.find_element(By.ID, 'mat-input-0')  # Using the ID for the email input field
email_field.clear()
email_field.send_keys(username)

# Find the password input field and enter your password
password_field = driver.find_element(By.XPATH, '//*[@id="mat-input-1"]')  # Using the ID for the password input field
password_field.clear()
password_field.send_keys(password)

# Submit the login form
password_field.send_keys(Keys.RETURN)

# Wait for login to complete and the page to load
time.sleep(10)  # Adjust this time depending on connection speed

# After logging in, navigate to the Web of Science home page
driver.get("https://www.webofscience.com/")

# Wait for the page to load
time.sleep(5)

# Step 1: Click on "Advanced Search"
advanced_search_link = driver.find_element(By.XPATH, '//a[@data-ta="advanced-search-link"]')
advanced_search_link.click()

# Wait for the advanced search page to load
time.sleep(5)

# Step 2: Locate the text area for search query and enter the search string
search_textarea = driver.find_element(By.ID, "advancedSearchInputArea")
driver.execute_script("arguments[0].scrollIntoView(true);", search_textarea)
time.sleep(1)  # Allow time for scrolling, adjust if necessary
search_textarea.clear()
search_query = "((AB=(social media)) AND AB=(gender)) AND AB=(conservative)"
search_textarea.send_keys(search_query)


# Use JavaScript to click the button directly
search_button = driver.find_element(By.XPATH, '/html/body/app-wos/main/div/div/div[2]/div/div/div[2]/app-input-route/app-search-home/div[2]/div[2]/app-input-route/app-search-advanced/app-advanced-search-form/form/div[3]/div[1]/div[1]/div/button[2]/span[1]')

# Trigger the click event using JavaScript
driver.execute_script("arguments[0].click();", search_button)

# Wait for the search results to load
time.sleep(5)

# Scrape article details (same logic as before)
articles = []
while True:
    # Parse the page content with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Wait for article links to be present (wait for the first article title link to load)
    article_links = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'title-link'))
    )
    
    # Scrape each article's title and URL
    for link in article_links:
        article_url = link.get_attribute('href')
        title = link.text.strip()
        
        # Visit article URL and get the abstract
        driver.get("https://www.webofscience.com" + article_url)  # Use the full URL for the article page
        time.sleep(2)
        article_soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Extract the abstract
        abstract_div = article_soup.find('div', class_='abstract--instance')  # Adjusted class for abstract div
        if abstract_div:
            abstract = abstract_div.find('p').get_text() if abstract_div.find('p') else "Abstract not found"
        else:
            abstract = "Abstract not found"
        
        # Store the article data
        articles.append({'title': title, 'url': "https://www.webofscience.com" + article_url, 'abstract': abstract})
        
    # Check if there's a next page
    next_button = soup.find('a', class_='next')
    if next_button:
        next_page_url = next_button.get('href')
        driver.get("https://www.webofscience.com" + next_page_url)  # Use the full URL for the next page
        time.sleep(5)
    else:
        break

# Output the articles
for article in articles:
    print(f"Title: {article['title']}")
    print(f"URL: {article['url']}")
    print(f"Abstract: {article['abstract']}")
    print("="*80)

# Close the WebDriver
driver.quit()