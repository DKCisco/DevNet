import subprocess

def ping_ips(input_file, success_file, failure_file):
    # Step 1: Read the IP addresses
    with open(input_file, 'r') as f:
        ips = f.readlines()
    
    for ip in ips:
        ip = ip.strip()  # Remove any extra whitespace or newline characters
        
        # Step 2: Ping the IP address
        response = subprocess.run(['ping', '-c', '1', ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Step 3: Log the results
        if response.returncode == 0:
            with open(success_file, 'a') as f:
                f.write(ip + '\n')
        else:
            with open(failure_file, 'a') as f:
                f.write(ip + '\n')

# Example usage:
ping_ips('input_ips.txt', 'successful_pings.txt', 'failed_pings.txt')
