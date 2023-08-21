import requests
import json
import maskpass
import os

# SolarWinds server details
SOLARWINDS_URL = 'https://solarwinds_url:17778/SolarWinds/InformationService/v3/Json/Query'
USERNAME = maskpass.askpass(prompt="Enter UN: ", mask="#*")
PASSWORD = maskpass.askpass(prompt="Enter PW: ", mask="#*")

# Load IP addresses from the file
with open("ip_addresses.txt", "r") as file:
    ip_addresses = [line.strip() for line in file if line.strip()]

print("IP addresses loaded:", ip_addresses)  # Debug print

# Update the SWQL query with the correct entity and columns
formatted_ip_addresses = ["'" + ip + "'" for ip in ip_addresses]
query = f"SELECT Caption, IPAddress FROM Cortex.Orion.Node WHERE IPAddress IN ({','.join(formatted_ip_addresses)})"

response = requests.post(SOLARWINDS_URL,
                         data=json.dumps({"query": query}),
                         headers={'Content-Type': 'application/json'},
                         auth=(USERNAME, PASSWORD),
                         verify=False)

print("API response received.")  # Debug print

output_path_json = os.path.join(os.getcwd(), "output.json")
with open(output_path_json, "w") as file:
    if response.status_code == 200:
        results = response.json()
        json.dump(results, file, indent=4)
    else:
        file.write(f"Error: {response.status_code} {response.text}\n")

print(f"Results written to {output_path_json}")  # Debug print
