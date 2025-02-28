import requests
from requests.auth import HTTPBasicAuth
import urllib3
import csv

# Suppress only the single InsecureRequestWarning from urllib3 needed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Replace these variables with your SolarWinds Orion server details and credentials
orion_server = 'solarwind_server.com'
username = 'api_user'
password = 'password'
subnet_address = input("Enter the subnet address (e.g., 10.190.7.0): ")

# SWIS API URL
url = f'https://{orion_server}:17774/SolarWinds/InformationService/v3/Json/Query'

# SWQL query
query = f"""
SELECT n.IPAddress, n.Description, n.Comments, n.DnsBackward
FROM IPAM.IPNode n
INNER JOIN IPAM.Subnet s ON n.SubnetId = s.SubnetId
WHERE s.Address = '{subnet_address}'
"""

# Request payload
payload = {
    'query': query
}

# Make the request
response = requests.post(url, json=payload, auth=HTTPBasicAuth(username, password), verify=False)

# Check for successful response
if response.status_code == 200:
    data = response.json()
    # Open a CSV file to write the results
    with open('ipam_results.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header row
        writer.writerow(['IPAddress', 'Description', 'Comments', 'DnsBackward'])
        # Write the data rows
        for item in data['results']:
            writer.writerow([item['IPAddress'], item['Description'], item['Comments'], item['DnsBackward']])
    print("Results have been written to ipam_results.csv")
else:
    print(f"Error: {response.status_code} - {response.text}")