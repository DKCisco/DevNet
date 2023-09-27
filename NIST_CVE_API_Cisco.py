import requests
import json
import base64
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType

# Define the base URL
base_url = "https://services.nvd.nist.gov/rest/json/cves/1.0"

# Define the CPE name for Cisco products
cisco_cpe_name = "cpe:2.3:o:cisco:ios:*:*:*:*:*:*:*"

# Create the full URL with the CPE query parameter
url = f"{base_url}?cpeName={cisco_cpe_name}"

# Make the API request
response = requests.get(url)

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Get the current date and time
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Define the filename with the date appended
    filename = f"cves_cisco_{current_datetime}.json"
    
    # Parse the JSON response
    data = response.json()
    
    # Save the JSON data to a file
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)
    
    print(f"JSON data related to Cisco devices saved to {filename}")

    # Prepare for email sending
    with open(filename, "rb") as f:
        data = f.read()
        encoded = base64.b64encode(data).decode()

    attachment = Attachment(
        FileContent(encoded),
        FileName(filename),
        FileType('application/json')
    )

    # Create the Mail object and append the attachment
    message = Mail(
        from_email='user@example.com',
        to_emails='user@example.com',
        subject='NIST CVE Data for Cisco',
        plain_text_content='Please find attached the NIST CVE data related to Cisco devices.'
    )
    message.attachment = attachment

    # Send the email
    try:
        sg = SendGridAPIClient('SG.XYZ')
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(f"Error sending email: {e}")

else:
    print(f"Failed to retrieve data. Status code: {response.status_code}")