import paramiko
import time
import maskpass

def ssh_connect(ip, username, password, delay=5):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    attempts = 0
    while True:
        try:
            client.connect(ip, username=username, password=password)
            print(f"Successfully connected to {ip} on attempt {attempts + 1}!")
            client.close()
            return f"Success on {ip} after {attempts + 1} attempts."
        except Exception as e:
            print(f"Attempt on {ip} failed attempt {attempts + 1} failed with error: {e}")
            attempts += 1
            time.sleep(delay)
            if attempts > 2:  # Limit the number of retries
                return f"Failed on {ip} after {attempts} attempts. Error: {e}"

def main():
    # Collect credentials
    USERNAME = input("Enter the username: ")
    PASSWORD = maskpass.askpass(prompt="Enter PW: ", mask="#*")

    # Read IP addresses from file
    with open("ip_addresses.txt", "r") as file:
        ip_addresses = file.readlines()
    ip_addresses = [ip.strip() for ip in ip_addresses]

    # Try connecting to each IP and save the result
    results = []
    for ip in ip_addresses:
        result = ssh_connect(ip, USERNAME, PASSWORD)
        results.append(result)

    # Write results to a file
    with open("results.txt", "w") as file:
        for result in results:
            file.write(result + "\n")

if __name__ == "__main__":
    main()
