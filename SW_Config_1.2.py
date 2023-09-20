import paramiko
import getpass
import time

def ssh_to_cisco(host, port, command_file):
    username = input("Enter your username: ")
    password = getpass.getpass("Enter your password: ")

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Connect to the switch
    ssh_client.connect(hostname=host, port=port, username=username, password=password)
    
    # Start an interactive shell session
    remote_conn = ssh_client.invoke_shell()
    time.sleep(1)  # give the shell a second to establish
    
    # Read commands from the file and execute
    with open(command_file, 'r') as file:
        commands = file.readlines()

    for command in commands:
        remote_conn.send(command + '\n')
        time.sleep(2)  # Wait for the command to execute and output to be returned
        output = remote_conn.recv(65535).decode()
        print(f"Command: {command.strip()}\nOutput: {output}\n{'-'*40}\n")

    # Close the connection
    remote_conn.close()
    ssh_client.close()

# Usage example
ssh_to_cisco('A.B.C.D', 22, 'conf.txt')
