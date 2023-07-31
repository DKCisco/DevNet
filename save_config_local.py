from netmiko import ConnectHandler
import maskpass

device_ip = input('Enter the device IP address: ' )
admin_creds = input('Enter the username: ')
admin_pw = maskpass.askpass(prompt="Enter PW: ", mask="#*")
admin_en = maskpass.askpass(prompt="Enter enable PW: ", mask="*#")
file_save_name = input('What do you want to save the file name as: ')

iosv_l2 = {
    'device_type': 'cisco_ios',
    'ip': device_ip,
    'username': admin_creds,
    'password': admin_pw,
    'secret' : admin_en
}
net_connect = ConnectHandler(**iosv_l2)
net_connect.enable()
output = net_connect.send_command('show run')
save_file = open(file_save_name + ".txt","w")
save_file.write(output)
save_file.close()
print (output)
net_connect.disconnect()