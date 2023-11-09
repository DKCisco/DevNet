# Read IP addresses from list1.txt and list2.txt
with open('list1.txt', 'r') as file1, open('list2.txt', 'r') as file2:
    ip_addresses1 = set(file1.read().splitlines())
    ip_addresses2 = set(file2.read().splitlines())

# Find IP addresses present in list1.txt but missing from list2.txt
missing_ips = ip_addresses1 - ip_addresses2

# Write the missing IPs to a new .txt file
with open('missing_ips.txt', 'w') as output_file:
    output_file.write('\n'.join(sorted(missing_ips)))

print(f"Found {len(missing_ips)} missing IP addresses. Saved to 'missing_ips.txt'.")
