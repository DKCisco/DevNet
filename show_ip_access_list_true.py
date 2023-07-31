from netmiko import ConnectHandler
import maskpass
import logging

# Configure logging to save output to a file
logging.basicConfig(filename='netmiko_debug.log', level=logging.DEBUG)

def run_script_on_device(device_ip, admin_creds, admin_pw):
    iosv_l2 = {
        'device_type': 'cisco_ios',
        'ip': device_ip,
        'username': admin_creds,
        'password': admin_pw,
        'global_delay_factor': 10,
    }

    try:
        net_connect = ConnectHandler(**iosv_l2)
        net_connect.enable()
        output = net_connect.send_command('show ip access-list | i 10.250.22')
        save_file_name = f"{device_ip}_True.txt" if '10.250.22' in output else f"{device_ip}_False.txt"
        save_file = open(save_file_name, "w")
        save_file.write(output)
        save_file.close()
        print(f"Output from {device_ip}:\n{output}")
        net_connect.disconnect()
    except Exception as e:
        print(f"Failed to connect to {device_ip}. Error: {e}")

if __name__ == "__main__":
    # Example list of IP addresses, you can modify this as needed
    ip_addresses = ["10.170.1.1", "10.170.1.6", "10.170.1.7", "10.170.1.30", "10.170.253.1", "10.170.253.2", "10.190.0.26", "10.190.1.34", "10.190.1.37", 
            "10.190.1.82", "10.250.0.234", "10.250.0.227", "10.250.0.228", "10.250.0.229", "10.250.1.7", "10.252.1.10", "10.252.1.11", "10.253.2.10"]
    admin_creds = input('Enter the username: ')
    admin_pw = maskpass.askpass(prompt="Enter PW: ", mask="#*")

    for ip in ip_addresses:
        run_script_on_device(ip, admin_creds, admin_pw)
