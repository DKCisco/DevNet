import re

def extract_unique_ips(input_file, output_file):
    # Regular expression to match IPv4 addresses
    ip_pattern = re.compile(r'(?:\d{1,3}\.){3}\d{1,3}')
    unique_ips = set()

    with open(input_file, 'r') as file:
        for line in file:
            # Find all IPs in the line
            ips = ip_pattern.findall(line)
            for ip in ips:
                # Optional: Validate each octet is <= 255
                if all(0 <= int(octet) <= 255 for octet in ip.split('.')):
                    unique_ips.add(ip)

    # Write unique IPs to output file
    with open(output_file, 'w') as file:
        for ip in sorted(unique_ips):
            file.write(ip + '\n')

# Example usage
extract_unique_ips('unsorted_ips.txt', 'unique_ips.txt')
