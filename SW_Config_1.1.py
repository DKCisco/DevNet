import paramiko
import time
import maskpass

def recv_all(channel, timeout=10):
    start_time = time.time()
    data = b""
    while True:
        if channel.recv_ready():
            recv_data = channel.recv(65535)
            data += recv_data
            start_time = time.time()
        elif time.time() - start_time > timeout:
            break
        else:
            time.sleep(1)
    return data

def push_config(ip, username, password, config_file):
    # Connect to the Cisco switch
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"Connecting to {ip}...")
        ssh.connect(ip, username=username, password=password, look_for_keys=False)

        # Open the configuration file
        print(f"Reading configuration from {config_file}...")
        with open(config_file, 'r') as file:
            config_text = file.read()

        # Start an SSH shell
        print("Starting SSH shell...")
        shell = ssh.invoke_shell()
        output = recv_all(shell)

        # Enter privileged mode
        #shell.send('enable\n')
        #shell.send(enable_password + '\n')
        time.sleep(1)
        output = recv_all(shell)

        # Send the configuration commands
        print("Entering configure terminal...")
        shell.send('configure terminal\n')
        time.sleep(1)
        output = recv_all(shell)

        # Read and send the configuration file in chunks
        with open(config_file, 'r') as file:
            print("Sending configuration...")
            while True:
                chunk = file.read(1024)
                if not chunk:
                    break
                shell.send(chunk)
                time.sleep(1)

        # Send "exit" to exit configuration terminal
        #shell.send('exit\n')
        time.sleep(1)

        # Capture the remaining output
        output = recv_all(shell)

        # Print the output
        print("Configuration Output:")
        print(output.decode('utf-8'))

    except paramiko.AuthenticationException:
        print("Authentication failed. Please check your credentials.")
    except paramiko.SSHException as ssh_ex:
        print(f"SSH error occurred: {ssh_ex}")
    except Exception as ex:
        print(f"An error occurred: {ex}")
    finally:
        # Close the SSH connection
        ssh.close()

# Usage example
ip_address = input('Enter IP address: ')  # IP address of the Cisco switch
username = input('Enter UN: ')  # SSH username
password = maskpass.askpass(prompt="Enter PW: ", mask="#*")  # SSH password
#enable_password = maskpass.askpass(prompt="Enter enable password: ", mask="#*")
config_file_path_1 = 'aaa_config_part_1.txt'  # Path to the configuration text file
config_file_path_2 = 'aaa_config_part_2.txt'  # Path to the configuration text file
config_file_path_2_1 = 'aaa_config_part_2_1.txt'  # Path to the configuration text file
config_file_path_2_2 = 'aaa_config_part_2_2.txt'  # Path to the configuration text file
config_file_path_3 = 'aaa_config_part_3.txt'  # Path to the configuration text file
config_file_path_4 = 'aaa_config_part_4.txt'  # Path to the configuration text file
config_file_path_5 = 'aaa_config_part_5.txt'  # Path to the configuration text file
config_file_path_6 = 'aaa_config_part_6.txt'  # Path to the configuration text file
config_file_path_7 = 'aaa_config_part_7.txt'  # Path to the configuration text file
config_file_path_8 = 'aaa_config_part_8.txt'  # Path to the configuration text file
config_file_path_9 = 'aaa_config_part_9.txt'  # Path to the configuration text file
config_file_path_snmp = 'snmp_config_1.txt'  # Path to the configuration text file

# Call the function with debugging
push_config(ip_address, username, password, config_file_path_1)
push_config(ip_address, username, password, config_file_path_2)
push_config(ip_address, username, password, config_file_path_2_1)
push_config(ip_address, username, password, config_file_path_2_2)
push_config(ip_address, username, password, config_file_path_3)
push_config(ip_address, username, password, config_file_path_4)
push_config(ip_address, username, password, config_file_path_5)
push_config(ip_address, username, password, config_file_path_6)
push_config(ip_address, username, password, config_file_path_7)
push_config(ip_address, username, password, config_file_path_8)
push_config(ip_address, username, password, config_file_path_9)
push_config(ip_address, username, password, config_file_path_snmp)