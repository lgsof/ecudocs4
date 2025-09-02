import time
import random
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from fake_useragent import UserAgent

# Function to set up Selenium WebDriver with a random User Agent using fake_useragent
def init_driver():
    options = Options()

    # Generate a random user-agent using fake_useragent
    ua = UserAgent()
    user_agent = ua.random  # Generate a random user-agent
    options.set_preference("general.useragent.override", user_agent)

    # Optional: Uncomment to run in headless mode
    # options.add_argument('--headless')

    # Initialize Firefox WebDriver
    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
    return driver

# Function to log into the site
def login(driver, login_url, username, password):
    driver.get(login_url)
    
    # Find the username and password fields and login button (modify selectors as needed)
    driver.find_element(By.ID, 'username_field').send_keys(username)
    driver.find_element(By.ID, 'password_field').send_keys(password)
    driver.find_element(By.ID, 'login_button').click()

    # Wait for login to complete (adjust the waiting time or use WebDriverWait for specific elements)
    time.sleep(5)

# Function to download documents
def download_documents(driver, base_url, document_ids):
    for doc_id in document_ids:
        document_url = f"{base_url}/{doc_id}"
        print(f"Accessing: {document_url}")
        
        # Access the document page
        driver.get(document_url)

        # Insert logic to download the document here (e.g., find download button and click)
        try:
            download_button = driver.find_element(By.ID, 'download_button')  # Update selector
            download_button.click()

            # Wait for the download to complete
            time.sleep(random.uniform(3, 6))  # Random delay to simulate human behavior

        except Exception as e:
            print(f"Failed to download document {doc_id}: {str(e)}")
        
        # Introduce random delay between requests
        time.sleep(random.uniform(2, 5))

if __name__ == "__main__":
    login_url = "https://example.com/login"  # Replace with actual login URL
    base_url = "https://example.com/documents"  # Replace with base URL for documents
    username = "your_username"  # Replace with actual username
    password = "your_password"  # Replace with actual password

    document_ids = ['doc123', 'doc124', 'doc125']  # Replace with actual document IDs

    # Initialize the driver and log in
    driver = init_driver()
    login(driver, login_url, username, password)

    # Start downloading documents
    download_documents(driver, base_url, document_ids)

    # Quit driver after processing
    driver.quit()

