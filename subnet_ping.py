import os

subnet = "192.168.1."

# Open the files in write mode, this will create the file if it does not exist
# and overwrite it if it does.
with open('successful_pings.txt', 'w') as success_file, open('failed_pings.txt', 'w') as fail_file:
    for i in range(1, 255):
        ip = subnet + str(i)
        response = os.system("ping -c 1 -W 1 " + ip + " > /dev/null 2>&1")
        if response == 0:
            print(ip, 'is up!', file=success_file)
        else:
            print(ip, 'is down!', file=fail_file)
