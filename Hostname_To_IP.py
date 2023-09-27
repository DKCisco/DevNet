import subprocess
import re

def get_ip_address(hostname):
    """Ping the hostname and retrieve the IP address."""
    try:
        # Use the ping command to get the IP. We'll ping only once.
        response = subprocess.check_output(["ping", "-c", "1", hostname])

        # Use a regular expression to extract the IP address.
        ip_address = re.search(r'(?<=\().*?(?=\))', response.decode('utf-8')).group(0)
        return ip_address
    except:
        return None

def main():
    # Open the input and output files.
    with open('hostnames.txt', 'r') as infile, open('ips.txt', 'w') as outfile:
        for line in infile:
            hostname = line.strip()
            ip_address = get_ip_address(hostname)
            if ip_address:
                outfile.write(f"{hostname}: {ip_address}\n")
            else:
                outfile.write(f"{hostname}: Failed to get IP\n")

if __name__ == "__main__":
    main()
