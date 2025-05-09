"""
Date modified: 5/9/2025
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, WebDriverException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
import csv
import os
from datetime import datetime
from itertools import product

# Define keyword lists
socialmedia_words = ["social media", "facebook", "instagram", "twitter", "tiktok", "influencer", "creator"]
gender_words = ["gender", "women", "girls", "feminism", "wife", "mom", "mother"]
political_words = ["conservative", "alt-right", "trad wife", "religion", "traditional", "family", "marriage",
                   "housewife", "tradwife", "tradwives", "republican", "right-wing", "domestic"]

# Metadata file
metadata_file = 'wos_metadata_log.csv'
if not os.path.exists(metadata_file):
    with open(metadata_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Keyword1', 'Keyword2', 'Keyword3', 'Timestamp', 'Result Count', 'Missed/Stale Count', 'Filename'])


def scrape_wos_articles(keyword1, keyword2, keyword3):
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"wos_{keyword1}_{keyword2}_{keyword3}_{timestamp}.csv".replace(" ", "_")
    
    # Setup WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    try:
        driver.get("https://www.webofscience.com/wos/woscc/advanced-search")
        time.sleep(10)

        search_textarea = driver.find_element(By.ID, "advancedSearchInputArea")
        driver.execute_script("arguments[0].scrollIntoView(true);", search_textarea)
        time.sleep(1)
        search_textarea.clear()

        search_query = f"((AB=({keyword1})) AND AB=({keyword2})) AND AB=({keyword3})"
        search_textarea.send_keys(search_query)

        search_button = driver.find_element(By.XPATH, '/html/body/app-wos/main/div/div/div[2]/div/div/div[2]/app-input-route/app-search-home/div[2]/div[2]/app-input-route/app-search-advanced/app-advanced-search-form/form/div[3]/div[1]/div[1]/div/button[2]/span[1]')
        driver.execute_script("arguments[0].click();", search_button)

        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[data-ta="summary-record-title-link"]'))
        )

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Title', 'URL', 'Authors', 'Year', 'Citations', 'Abstract']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            total_articles = 0
            page_number = 1

            stale_exceptions = 0  # Counter for stale elements

            while True:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'app-record.Summary-record-view'))
                )

                results = driver.find_elements(By.CSS_SELECTOR, 'app-record.Summary-record-view')
                for result in results:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", result)
                        time.sleep(0.5)

                        title_tag = result.find_element(By.CSS_SELECTOR, '*[data-ta="summary-record-title-link"]')
                        title = title_tag.text.strip()
                        url = title_tag.get_attribute('href')
                        if url.startswith('/'):
                            url = f"https://www.webofscience.com{url}"

                        authors_elements = result.find_elements(By.CSS_SELECTOR, 'a.authors span')
                        authors = [a.text.strip() for a in authors_elements]

                        try:
                            pub_year = result.find_element(By.CSS_SELECTOR, 'span[data-ta="summary-record-pubdate"]').text.strip()
                        except NoSuchElementException:
                            pub_year = "N/A"

                        try:
                            citations = result.find_element(By.CSS_SELECTOR, 'a[data-ta="stat-number-citation-related-count"]').text.strip()
                        except NoSuchElementException:
                            citations = "0"

                        try:
                            show_more_button = result.find_element(By.CSS_SELECTOR, 'button.show-more-text')
                            driver.execute_script("arguments[0].click();", show_more_button)
                            time.sleep(0.5)
                        except NoSuchElementException:
                            pass

                        try:
                            abstract_el = result.find_element(By.CSS_SELECTOR, 'span.abstract-size p')
                            abstract = abstract_el.text.strip()
                        except NoSuchElementException:
                            abstract = "Abstract not found"

                        writer.writerow({
                            'Title': title,
                            'URL': url,
                            'Authors': ', '.join(authors),
                            'Year': pub_year,
                            'Citations': citations,
                            'Abstract': abstract
                        })

                        total_articles += 1

                    except StaleElementReferenceException:
                        stale_exceptions += 1
                        continue
                    except Exception as e:
                        print(f"Error processing an article: {e}")
                        continue

                try:
                    next_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-ta="next-page-button"]'))
                    )
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", next_button)
                    page_number += 1
                except Exception:
                    break  # No more pages

        # Log metadata
        with open(metadata_file, 'a', newline='', encoding='utf-8') as metafile:
            writer = csv.writer(metafile)
            writer.writerow([keyword1, keyword2, keyword3, timestamp, total_articles, stale_exceptions, filename])

    except Exception as e:
        print(f"Failed for {keyword1}, {keyword2}, {keyword3}: {e}")
    finally:
        driver.quit()


# Run the script over all combinations
for kw1, kw2, kw3 in product(socialmedia_words, gender_words, political_words):
    print(f"\nRunning combination: {kw1}, {kw2}, {kw3}")
    scrape_wos_articles(kw1, kw2, kw3)
