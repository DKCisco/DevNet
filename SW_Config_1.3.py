import paramiko
import getpass
import time

# Function to log SSH failures
def log_ssh_failure(ip, error_message, log_path):
    with open(log_path, 'a') as log_file:
        log_file.write(f"{ip} - {error_message}\n")

# ssh_to_switch function with try-except for logging and command output capture
def ssh_to_switch(ip, username, password, commands, log_path):
    output = ""  # Initialize output string
    try:
        print(f"Connecting to {ip}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password)

        channel = ssh.invoke_shell()
        response = channel.recv(10000).decode('utf-8')
        output += f"Initial response from {ip}: {response}\n"  # Append initial response to output

        channel.send('enable\n')
        time.sleep(1)

        channel.send('conf t\n')
        time.sleep(1)

        for command in commands:
            print(f"Sending command to {ip}: {command}")
            channel.send(command + "\n")
            time.sleep(10)  # Delay before sending next command
        
        channel.close()
        ssh.close()
    except Exception as e:
        error_message = str(e)
        print(f"Failed to connect to {ip}. Error: {error_message}")
        log_ssh_failure(ip, error_message, log_path)
        output += f"Failed to connect to {ip}. Error: {error_message}\n"
    return output  # Return the collected output

def main():
    username = input("Enter your username: ")
    password = getpass.getpass("Enter your password: ")
    log_file_path = 'ssh_failures.txt'
    commands = ['int range gig 1/0/1 - 48',
                'do wr mem']

    with open('ip_addresses.txt', 'r') as file:
        ip_addresses = [line.strip() for line in file.readlines()]

    with open('output.txt', 'a') as file:
        for ip in ip_addresses:
            output = ssh_to_switch(ip, username, password, commands, log_file_path)
            file.write("\n" + "="*50 + "\n")  # Corrected line separators
            file.write(output)
            file.write("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()
