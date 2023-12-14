import requests
import time
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_email(subject, content):
    message = Mail(
        from_email='from_email@example.com',  # Replace with your email
        to_emails='to_email@example.com',  # Replace with recipient email
        subject=subject,
        html_content=content)
    try:
        sg = SendGridAPIClient('your_sendgrid_api_key')  # Replace with your API key
        response = sg.send(message)
        print(f"Email sent with status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending email: {e}")

def check_https_status(websites):
    last_status = {}
    while True:
        for website in websites:
            try:
                response = requests.get(website, verify=False)
                current_status = response.status_code
                print(f"The website {website} is up with status code: {current_status}")

                # Check for status change
                if website in last_status and last_status[website] != current_status:
                    send_email("Website Status Changed",
                               f"The status of {website} changed from {last_status[website]} to {current_status}")

                last_status[website] = current_status

            except requests.exceptions.RequestException as err:
                print(f"Error occurred for website {website}: {err}")
                if website in last_status and last_status[website] != 'DOWN':
                    send_email("Website Down", f"The website {website} is down: {err}")
                last_status[website] = 'DOWN'
        
        time.sleep(60)

# List of websites to check
websites = ["https://www.bellco.org", "https://www.bethpagefcu.com/", "https://www.secumd.org/", "https://www.google.com/"]

# Suppress only the single InsecureRequestWarning from urllib3 needed
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

check_https_status(websites)
