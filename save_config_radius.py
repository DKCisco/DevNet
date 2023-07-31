from netmiko import ConnectHandler
import maskpass
import logging

device_ip = input('Enter the device IP address: ')
admin_creds = input('Enter the username: ')
admin_pw = maskpass.askpass(prompt="Enter PW: ", mask="#*")
file_save_name = input('What do you want to save the file name as: ')

iosv_l2 = {
    'device_type': 'cisco_ios',
    'ip': device_ip,
    'username': admin_creds,
    'password': admin_pw,
    'global_delay_factor': 10,
}

# Configure logging to save output to a file
logging.basicConfig(filename='netmiko_debug.log', level=logging.DEBUG)

net_connect = ConnectHandler(**iosv_l2)
net_connect.enable()
output = net_connect.send_command('show run')
save_file = open(file_save_name + ".txt", "w")
save_file.write(output)
save_file.close()
print(output)
net_connect.disconnect()