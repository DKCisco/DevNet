
from netmiko import ConnectHandler
import maskpass
import logging

# Configure logging to save output to a file
logging.basicConfig(filename='netmiko_debug.log', level=logging.DEBUG)

def run_script_on_device(device_ip, admin_creds_list, admin_pw, failed_attempts):
    iosv_l2 = {
        'device_type': 'cisco_ios',
        'ip': device_ip,
        'global_delay_factor': 10,
    }

    for admin_creds in admin_creds_list:
        iosv_l2['username'] = admin_creds
        iosv_l2['password'] = admin_pw

        try:
            net_connect = ConnectHandler(**iosv_l2)
            net_connect.enable()
            output = net_connect.send_command('show ip access-list | b VTY_Internal_ACL')
            net_connect.disconnect()

            # Determine whether '10.250.6.0' is in the output
            is_true = '0.0.1.255' in output

            # Create the appropriate file name based on the 'is_true' value
            save_file_name = "True.txt" if is_true else "False.txt"
            with open(save_file_name, "a") as save_file:
                save_file.write(f"IP address: {device_ip}\n{output}\n")

            print(f"Output from {device_ip}:\n{output}")
            break  # Connection successful, exit the loop
        except Exception as e:
            error_message = f"Failed to connect to or authenticate with {device_ip} using username '{admin_creds}'. Error: {e}"
            print(error_message)
            failed_attempts.append(error_message)  # Add the error message to the list

if __name__ == "__main__":
    # Example list of IP addresses, you can modify this as needed
    ip_addresses = []
    with open('to_do.txt', 'r') as f:
        for line in f:
            ip_addresses.append(line.strip())
    admin_creds_list = (input('Enter the username(s) separated by commas: ').split(','))
    admin_pw = maskpass.askpass(prompt="Enter PW: ", mask="#*")

    # List to store failed attempts
    failed_attempts = []

    for ip in ip_addresses:
        run_script_on_device(ip, admin_creds_list, admin_pw, failed_attempts)

    # After trying all IPs, write failed attempts to a text file
    with open("failed.txt", "w") as f:
        for error_message in failed_attempts:
            f.write(error_message + "\n")

