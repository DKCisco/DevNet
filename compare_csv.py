import csv

# Read IP addresses from ExportCP.csv
export_cp_ips = set()
with open('ExportCP.csv', 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        export_cp_ips.add(row['IP_Address'])

# Read IP addresses from Devices.csv
four_leaf_ips = set()
with open('Devices1.csv', 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        four_leaf_ips.add(row['IP Address'])

# Find IP addresses missing from ExportCP.csv
missing_ips = four_leaf_ips - export_cp_ips

# Print the missing IP addresses
print("IP addresses missing from ExportCP.csv:")
for ip in missing_ips:
    print(ip)