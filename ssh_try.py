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
            return
        except Exception as e:
            print(f"Attempt {attempts + 1} failed with error: {e}")
            attempts += 1
            time.sleep(delay)

# Replace the following values with your SSH credentials
IP_ADDRESS = input("Enter the IP address: ")
USERNAME = input("Enter the username: ")
PASSWORD = maskpass.askpass(prompt="Enter PW: ", mask="#*")

ssh_connect(IP_ADDRESS, USERNAME, PASSWORD)
