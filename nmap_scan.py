import nmap
import os

# Initialize the nmap scanner
nm = nmap.PortScanner()

# Read IP addresses from the file
with open('Active_IPs.txt', 'r') as file:
    ip_list = file.read().splitlines()

# Open the output files in write mode
with open('scan_results.txt', 'w') as scan_file, open('scan_failures.txt', 'w') as fail_file:
    for ip in ip_list:
        # Log the current IP being processed
        scan_file.write(f'Processing IP: {ip}\n')
        fail_file.write(f'Processing IP: {ip}\n')

        # Ping the IP address
        response = os.system(f'ping -c 1 {ip}')

        if response == 0:
            try:
                # Perform the scan
                nm.scan(ip, arguments='-O')

                # Get the OS information
                os_info = nm[ip]['osclass'][0]['osfamily'] if 'osclass' in nm[ip] else 'OS not detected'
                device_type = nm[ip]['osclass'][0]['type'] if 'osclass' in nm[ip] else 'Device type not detected'

                # Write the results to the file
                scan_file.write(f'IP Address: {ip}\n')
                scan_file.write(f'OS: {os_info}\n')
                scan_file.write(f'Device Type: {device_type}\n\n')
            except Exception as e:
                fail_file.write(f'Error scanning {ip}: {str(e)}\n\n')
        else:
            fail_file.write(f'Ping failed for {ip}\n')

print("Scan complete. Results saved to scan_results.txt and failures.txt")
