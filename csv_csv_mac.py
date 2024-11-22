import csv

# Read the first CSV file and store its content in a dictionary
first_csv_data = {}
with open('ap_ip.csv', mode='r') as file:
    reader = csv.reader(file)
    for row in reader:
        if len(row) < 2:
            continue  # Skip rows that don't have at least 2 columns
        name = row[0]
        ip_address = row[1]
        first_csv_data[name] = ip_address

# Open the second CSV file and the output CSV file
with open('ap1.csv', mode='r') as second_file, open('output_csv.csv', mode='a', newline='') as output_file:
    reader = csv.reader(second_file)
    writer = csv.writer(output_file)
    
    # Write header to the output CSV file
    writer.writerow(['Client_Name', 'Client_IP_Address', 'MAC_Address'])
    
    # Iterate through the second CSV file and find the corresponding MAC address from the first CSV file
    for row in reader:
        if len(row) < 2:
            continue  # Skip rows that don't have at least 2 columns
        client_name = row[0]
        mac_address = row[1]
        if client_name in first_csv_data:
            client_ip = first_csv_data[client_name]
            # Write the result to the output CSV file
            writer.writerow([client_name, client_ip, mac_address])

print("Comparison complete. The results are saved in 'output_csv.csv'.")