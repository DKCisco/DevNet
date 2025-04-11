import subprocess
import smtplib
from email.mime.text import MIMEText
import maskpass
import paramiko
import logging

# Enable verbose logging
logging.basicConfig(level=logging.DEBUG)

# Function to run the command on a remote host and check the output
def check_switch_output(ip, username, password):
    command = "sh int status | i notconnect"
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ip, username=username, password=password, allow_agent=False)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        ssh.close()
        return output, None
    except Exception as e:
        return None, str(e)

# Main function
def main():
    # Read the list of IP addresses from a file
    with open('ip_addresses.txt', 'r') as f:
        ip_addresses = f.read().splitlines()

    switch_username = input("Enter switch SSH username: ")
    switch_password = maskpass.askpass("Enter switch SSH password: ")

    for ip in ip_addresses:
        output, error = check_switch_output(ip, switch_username, switch_password)
        
        if output:
            if "notconnect" in output:
                with open('matching_output_log.txt', 'a') as log_file:
                    log_file.write(f"The Cisco switch at IP {ip} returned the following output:\n\n{output}\n")
                print(f"Logged matching output for IP {ip}.")
            else:
                print(f"The output for IP {ip} did not match the expected pattern.")
        else:
            with open('error_log.txt', 'a') as log_file:
                log_file.write(f"Failed to SSH to IP {ip}: {error}\n")
            print(f"Failed to SSH to IP {ip}. Logged the failure.")

if __name__ == "__main__":
    main()