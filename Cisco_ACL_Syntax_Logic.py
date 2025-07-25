from netmiko import ConnectHandler
import maskpass
import logging
from datetime import datetime
import os

# Create a timestamp for unique file naming
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Configure logging to save debug output to a file
logging.basicConfig(filename='netmiko_debug.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def run_script_on_device(device_ip, admin_creds_list, admin_pw, failed_attempts, search_strings):
    """
    Connects to a network device, runs a command, and logs output based on search strings.

    Args:
        device_ip (str): The IP address of the device to connect to.
        admin_creds_list (list): A list of usernames to attempt for authentication.
        admin_pw (str): The password for authentication.
        failed_attempts (list): A list to store error messages for failed connections.
        search_strings (list): A list of strings to search for in the command output.
    """
    # Device connection parameters for Netmiko
    device_params = {
        'device_type': 'cisco_ios', # Generic Cisco IOS device type
        'ip': device_ip,
        'global_delay_factor': 10,  # Increase delay factor for slower devices/connections
    }

    # Iterate through each username to attempt connection
    for admin_creds in admin_creds_list:
        device_params['username'] = admin_creds
        device_params['password'] = admin_pw

        try:
            # Establish SSH connection
            print(f"Attempting to connect to {device_ip} with username '{admin_creds}'...")
            net_connect = ConnectHandler(**device_params)
            net_connect.enable() # Enter enable mode
            
            # Send the command and capture output
            print(f"Running command on {device_ip}...")
            output = net_connect.send_command('show ip access-list | b SNMP_ACL')
            net_connect.disconnect() # Disconnect from the device

            # Check if any of the search strings are present in the output
            found_any_string = False
            for s_string in search_strings:
                if s_string in output:
                    found_any_string = True
                    break # Found at least one, no need to check further

            # Determine the appropriate file name based on whether strings were found
            if found_any_string:
                save_file_name = f"SNMP_Found_{timestamp}.txt"
            else:
                save_file_name = f"SNMP_NotFound_{timestamp}.txt"
            
            # Define the output directory and ensure it exists
            output_dir = "SNMP_Output_Files"
            os.makedirs(output_dir, exist_ok=True) # Create directory if it doesn't exist
            full_path = os.path.join(output_dir, save_file_name) # Full path for the output file

            # Write the device IP and command output to the determined file
            with open(full_path, "a") as save_file:
                save_file.write(f"--- Device IP: {device_ip} ---\n")
                save_file.write(f"{output}\n\n")

            print(f"Output from {device_ip} processed. Saved to: {full_path}")
            break  # Connection and processing successful, exit the username loop
        except Exception as e:
            # Log and print error message for failed attempts
            error_message = (f"Failed to connect to or authenticate with {device_ip} "
                             f"using username '{admin_creds}'. Error: {e}")
            logging.error(error_message) # Log the error
            print(error_message)
            failed_attempts.append(error_message) # Add error to failed attempts list
    else:
        # This 'else' block executes if the loop completes without a 'break'
        # meaning all usernames failed for the current device.
        print(f"All authentication attempts failed for {device_ip}.")

if __name__ == "__main__":
    # List to store IP addresses read from a file
    ip_addresses = []
    try:
        with open('BL_2960.txt', 'r') as f:
            for line in f:
                ip_addresses.append(line.strip()) # Read each IP, remove whitespace
    except FileNotFoundError:
        print("Error: 'BL_2960.txt' not found. Please create this file with one IP per line.")
        exit() # Exit if the IP list file is not found

    # Prompt user for usernames (comma-separated) and password
    admin_creds_list = input('Enter the username(s) separated by commas: ').split(',')
    admin_pw = maskpass.askpass(prompt="Enter PW: ", mask="#*")

    # Define the list of strings to search for in the command output
    # Customize this list with the specific strings you need to find.
    search_strings = ['10.189.', '192.168.', '172.16.', '10.10.10.'] 

    # List to store error messages for devices that could not be connected to
    failed_attempts = []

    # Iterate through each IP address and run the script
    for ip in ip_addresses:
        run_script_on_device(ip, admin_creds_list, admin_pw, failed_attempts, search_strings)

    # After processing all IPs, write any failed attempts to a separate log file
    if failed_attempts:
        failed_log_path = os.path.join("SNMP_Output_Files", f"{timestamp}_failed_connections.txt")
        with open(failed_log_path, "w") as f_failed:
            f_failed.write("--- Failed Connection Attempts ---\n")
            for error_message in failed_attempts:
                f_failed.write(error_message + "\n")
        print(f"\nSummary: {len(failed_attempts)} device(s) failed to connect. See '{failed_log_path}' for details.")
    else:
        print("\nSummary: All devices processed successfully with no connection failures.")
