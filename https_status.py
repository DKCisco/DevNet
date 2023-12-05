import requests
import time

def check_https_status(websites):
    while True:
        for website in websites:
            try:
                # Ignore SSL certificate validation
                response = requests.get(website, verify=False)
                print(f"The website {website} is up with status code: {response.status_code}")
            except requests.exceptions.RequestException as err:
                print(f"Error occurred for website {website}: {err}")
        
        # Sleep for a specified time (e.g., 60 seconds) before the next iteration
        time.sleep(1)

# List of websites to check
websites = ["https://url.com"]

# Suppress only the single InsecureRequestWarning from urllib3 needed
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

check_https_status(websites)
