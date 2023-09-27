import time
def read_from_channel(channel):
    output = ""
    while True:
        if channel.recv_ready():
            output += channel.recv(65535).decode()
        else:
            time.sleep(2)
            if not channel.recv_ready():
                break
    return output

import paramiko
import maskpass
import time

device_ip = input('Enter the device IP address: ')
is_local_login = input('Is this a local login? (yes/no): ').strip().lower()

if is_local_login == 'yes':
    admin_creds = input('Enter the username for local login: ')
    admin_pw = maskpass.askpass(prompt="Enter PW for local login: ", mask="#*")
    admin_en = maskpass.askpass(prompt="Enter enable PW: ", mask="*#")
else:
    admin_creds = input('Enter the username for non-local login: ')
    admin_pw = maskpass.askpass(prompt="Enter PW for non-local login: ", mask="#*")
    admin_en = None

file_save_name = input('What do you want to save the file name as: ')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(device_ip, username=admin_creds, password=admin_pw, look_for_keys=False, allow_agent=False)

# Using Paramiko's invoke_shell method to interact with the device
channel = ssh.invoke_shell()

if is_local_login == 'yes':
    # Sending enable command for local login
    channel.send('enable\n')
    time.sleep(1)  # Waiting for the enable password prompt
    channel.send(admin_en + '\n')
    time.sleep(1)  # Waiting for the command to be processed

# Setting terminal length to avoid pagination and fetching running config
channel.send('terminal length 0\n')
time.sleep(1)
channel.send('show run\n')
time.sleep(2)  # Giving some time for the command to execute

# Capturing the output
output = read_from_channel(channel)

# Closing the SSH connection
ssh.close()

# Saving the output to a file
with open(file_save_name + ".txt", "w") as file:
    file.write(output)

print(output)
