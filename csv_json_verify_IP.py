import csv
import json

# Function to read CSV file and return a list of dictionaries
def read_csv(file_path):
    with open(file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        return [row for row in csv_reader]

# Function to read JSON file and return the data
def read_json(file_path):
    with open(file_path, mode='r') as file:
        return json.load(file)

# Function to write mismatched entries to a new CSV file
def write_mismatched_csv(file_path, mismatched_entries):
    with open(file_path, mode='w', newline='') as file:
        fieldnames = ['Client_Name', 'Client_IP_Address', 'Current_IP_Address']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for entry in mismatched_entries:
            writer.writerow(entry)

# Paths to the input files
csv_file_path = 'Client_Name,Client_IP_Address.csv'
json_file_path = 'org_data_1.json'
output_csv_file_path = 'mismatched_clients.csv'

# Read the CSV and JSON files
csv_data = read_csv(csv_file_path)
json_data = read_json(json_file_path)

# Check for mismatches and collect them
mismatched_entries = []
for csv_entry in csv_data:
    client_name = csv_entry['Client_Name']
    client_ip = csv_entry['Client_IP_Address']
    
    # Find the corresponding entry in the JSON data
    json_entry = next((item for item in json_data if item['name'] == client_name), None)
    
    # If the IP addresses do not match, add to mismatched entries
    if json_entry and json_entry['lanIp'] != client_ip:
        mismatched_entries.append({
            'Client_Name': client_name,
            'Client_IP_Address': client_ip,
            'Current_IP_Address': json_entry['lanIp']
        })

# Write the mismatched entries to a new CSV file
write_mismatched_csv(output_csv_file_path, mismatched_entries)

print(f"Mismatched entries have been written to {output_csv_file_path}.")