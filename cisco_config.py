import netmiko
import getpass
import os
import datetime
import subprocess
import csv
import re # For regular expressions to parse show command output

def run_commands_and_extract_info(input_csv_file, commands):
    """
    Connects to Cisco switches via SSH, runs commands, extracts specific info,
    and logs results to CSV and text files.

    Args:
        input_csv_file (str): Path to a CSV file with 'Hostname' and 'IP Address' columns.
        commands (list): A list of commands to execute on the switches.
                         Can contain {IP_ADDR_VAR} for the device's own IP.
                         {INTERFACE_NAME_VAR} will be dynamically replaced after discovery.
    """

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    main_log_file = f"cisco_ssh_main_log_{timestamp}.txt"
    error_log_file = "error_output.txt"
    output_csv_file = f"processed_devices_{timestamp}.csv" # New timestamped CSV for output

    print(f"Logging main output to: {main_log_file}")
    print(f"Logging errors to: {error_log_file}")
    print(f"Logging processed data to CSV: {output_csv_file}\n")

    username = input("Enter SSH username: ")
    password = getpass.getpass("Enter SSH password: ")

    devices_data = []

    # 1. Read input CSV
    try:
        with open(input_csv_file, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            if 'Hostname' not in reader.fieldnames or 'IP Address' not in reader.fieldnames:
                raise ValueError("Input CSV must contain 'Hostname' and 'IP Address' columns.")
            for row in reader:
                # Initialize new columns for each device
                row['Status'] = 'Pending'
                row['Error Message'] = ''
                row['IOS Version'] = ''
                row['Serial Number'] = ''
                row['Interface Name'] = '' # New column for the interface
                row['Base MAC Address'] = ''
                devices_data.append(row)
    except FileNotFoundError:
        print(f"Error: Input CSV file '{input_csv_file}' not found.")
        with open(error_log_file, 'a') as f_error:
            f_error.write(f"{datetime.datetime.now()}: Error: Input CSV file '{input_csv_file}' not found.\n")
        return
    except ValueError as ve:
        print(f"Error reading CSV: {ve}")
        with open(error_log_file, 'a') as f_error:
            f_error.write(f"{datetime.datetime.now()}: Error reading CSV: {ve}\n")
        return
    except Exception as e:
        print(f"An unexpected error occurred while reading CSV: {e}")
        with open(error_log_file, 'a') as f_error:
            f_error.write(f"{datetime.datetime.now()}: Error reading CSV: {e}\n")
        return

    # Prepare for writing output CSV after processing all devices
    # Ensure all possible new columns are in the header
    output_fieldnames = list(devices_data[0].keys()) if devices_data else []
    additional_fields = ['Status', 'Error Message', 'IOS Version', 'Serial Number', 'Interface Name', 'Base MAC Address', 'Last Command Output']
    for field in additional_fields:
        if field not in output_fieldnames:
            output_fieldnames.append(field)


    with open(main_log_file, 'a') as f_main_log, open(error_log_file, 'a') as f_error_log:
        for device in devices_data:
            hostname = device.get('Hostname', 'N/A')
            ip_address = device.get('IP Address', 'N/A')
            
            # Reset values for each iteration in case of previous failures
            device['Status'] = 'Pending'
            device['Error Message'] = ''
            device['IOS Version'] = ''
            device['Serial Number'] = ''
            device['Interface Name'] = ''
            device['Base MAC Address'] = ''
            device['Last Command Output'] = ''


            f_main_log.write(f"--- Processing Device: {hostname} ({ip_address}) ---\n")
            print(f"--- Processing Device: {hostname} ({ip_address}) ---")

            # 1. Ping the IP address
            f_main_log.write(f"Attempting to ping {ip_address}...\n")
            print(f"Attempting to ping {ip_address}...")
            try:
                if os.name == 'nt':
                    ping_command = ['ping', '-n', '1', ip_address]
                else:
                    ping_command = ['ping', '-c', '1', ip_address]

                ping_output = subprocess.run(
                    ping_command, capture_output=True, text=True, timeout=10
                )
                f_main_log.write(f"Ping Result:\n{ping_output.stdout}\n{ping_output.stderr}\n")
                print(f"Ping Result:\n{ping_output.stdout}")

                if ping_output.returncode != 0:
                    device['Status'] = 'Ping Failed'
                    device['Error Message'] = f"Ping failed: {ping_output.stderr.strip() or ping_output.stdout.strip()}"
                    f_main_log.write(f"Ping to {ip_address} failed. Skipping SSH attempt.\n\n")
                    print(f"Ping to {ip_address} failed. Skipping SSH attempt.\n")
                    f_error_log.write(f"{datetime.datetime.now()}: Ping failed for {hostname} ({ip_address})\n")
                    continue

            except subprocess.TimeoutExpired:
                device['Status'] = 'Ping Timeout'
                device['Error Message'] = "Ping timed out."
                f_main_log.write(f"Ping to {ip_address} timed out. Skipping SSH attempt.\n\n")
                print(f"Ping to {ip_address} timed out. Skipping SSH attempt.\n")
                f_error_log.write(f"{datetime.datetime.now()}: Ping timed out for {hostname} ({ip_address})\n")
                continue
            except Exception as e:
                device['Status'] = 'Ping Error'
                device['Error Message'] = f"Ping error: {e}"
                f_main_log.write(f"Error during ping to {ip_address}: {e}. Skipping SSH attempt.\n\n")
                print(f"Error during ping to {ip_address}: {e}. Skipping SSH attempt.\n")
                f_error_log.write(f"{datetime.datetime.now()}: Ping error for {hostname} ({ip_address}): {e}\n")
                continue

            # 2. Attempt SSH connection
            f_main_log.write(f"Attempting SSH connection to {ip_address}...\n")
            print(f"Attempting SSH connection to {ip_address}...")
            device_params = {
                "device_type": "cisco_ios",
                "host": ip_address,
                "username": username,
                "password": password,
                "secret": password, # For privilege mode if needed
            }

            try:
                with netmiko.ConnectHandler(**device_params) as net_connect:
                    f_main_log.write(f"Successfully connected to {hostname} ({ip_address})\n")
                    print(f"Successfully connected to {hostname} ({ip_address})")

                    if not net_connect.check_enable_mode():
                        net_connect.enable()
                        f_main_log.write("Entered enable mode.\n")
                        print("Entered enable mode.")

                    show_version_output = ""
                    show_ip_int_brief_output_for_ip = ""
                    show_interface_detail_output = ""
                    last_command_output = "" # For the CSV column

                    # Execute commands one by one
                    for i, command_template in enumerate(commands):
                        command_to_execute = command_template

                        # Handle dynamic variables
                        if "{IP_ADDR_VAR}" in command_template:
                            command_to_execute = command_template.replace("{IP_ADDR_VAR}", ip_address)
                        elif "{INTERFACE_NAME_VAR}" in command_template:
                            # This command should only be executed if interface name is known
                            if not device['Interface Name']:
                                f_main_log.write(f"Skipping command '{command_template}': Interface name not yet discovered for {ip_address}.\n")
                                print(f"Skipping command '{command_template}': Interface name not yet discovered for {ip_address}.")
                                continue
                            command_to_execute = command_template.replace("{INTERFACE_NAME_VAR}", device['Interface Name'])

                        f_main_log.write(f"Executing command: {command_to_execute}\n")
                        print(f"Executing command: {command_to_execute}")
                        output = net_connect.send_command(command_to_execute)
                        f_main_log.write(f"Command Output:\n{output}\n")
                        print(f"Command Output:\n{output}")

                        # Store specific command outputs for parsing
                        if "show version" in command_to_execute.lower() and "terminal length" not in command_to_execute.lower():
                            show_version_output = output
                        if "show ip interface brief" in command_to_execute.lower() and ip_address in command_to_execute:
                            show_ip_int_brief_output_for_ip = output
                        if "show interface" in command_to_execute.lower() and device['Interface Name'] and device['Interface Name'] in command_to_execute:
                            show_interface_detail_output = output

                        # If this is the last command in the original list, store its output for CSV's "Last Command Output"
                        if i == len(commands) - 1:
                            last_command_output = output.strip()

                    # --- After all commands, perform parsing ---
                    device['IOS Version'] = parse_ios_version(show_version_output)
                    device['Serial Number'] = parse_serial_number(show_version_output)

                    # Extract Interface Name (crucial for subsequent MAC discovery)
                    extracted_interface = parse_interface_name(show_ip_int_brief_output_for_ip, ip_address)
                    device['Interface Name'] = extracted_interface

                    # Now, if we found an interface, we can try to get its MAC
                    if extracted_interface:
                        # Re-run or specifically run 'show interface <interface_name>' to get MAC
                        f_main_log.write(f"Dynamically executing: show interface {extracted_interface}\n")
                        print(f"Dynamically executing: show interface {extracted_interface}")
                        mac_detail_output = net_connect.send_command(f"show interface {extracted_interface}")
                        f_main_log.write(f"Command Output (show interface {extracted_interface}):\n{mac_detail_output}\n")
                        print(f"Command Output (show interface {extracted_interface}):\n{mac_detail_output}")
                        device['Base MAC Address'] = parse_mac_from_show_interface(mac_detail_output)
                    else:
                        f_main_log.write(f"Could not determine primary interface for {ip_address}. Skipping MAC address retrieval.\n")
                        print(f"Could not determine primary interface for {ip_address}. Skipping MAC address retrieval.")
                        device['Base MAC Address'] = "N/A - Interface Not Found"


                    device['Status'] = 'Success'
                    device['Last Command Output'] = last_command_output # Assign the last command's output

            except netmiko.NetmikoTimeoutException:
                device['Status'] = 'SSH Timeout'
                device['Error Message'] = "SSH connection timed out."
                f_main_log.write(f"SSH connection to {ip_address} timed out.\n\n")
                print(f"SSH connection to {ip_address} timed out.\n")
                f_error_log.write(f"{datetime.datetime.now()}: SSH timeout for {hostname} ({ip_address})\n")
            except netmiko.NetmikoAuthenticationException:
                device['Status'] = 'Authentication Failed'
                device['Error Message'] = "SSH authentication failed."
                f_main_log.write(f"SSH authentication failed for {ip_address}.\n\n")
                print(f"SSH authentication failed for {ip_address}.\n")
                f_error_log.write(f"{datetime.datetime.now()}: SSH authentication failed for {hostname} ({ip_address})\n")
            except Exception as e:
                device['Status'] = 'SSH Error'
                device['Error Message'] = f"Unexpected SSH error: {e}"
                f_main_log.write(f"An unexpected SSH error occurred for {ip_address}: {e}\n\n")
                print(f"An unexpected SSH error occurred for {ip_address}: {e}\n")
                f_error_log.write(f"{datetime.datetime.now()}: Unexpected SSH error for {hostname} ({ip_address}): {e}\n")

    # 3. Write all collected data to the new CSV
    try:
        with open(output_csv_file, mode='w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=output_fieldnames)
            writer.writeheader()
            writer.writerows(devices_data)
        print(f"\nSuccessfully wrote all processed data to {output_csv_file}")
    except Exception as e:
        print(f"Error writing output CSV file: {e}")
        with open(error_log_file, 'a') as f_error:
            f_error.write(f"{datetime.datetime.now()}: Error writing output CSV file: {e}\n")

# --- Parsing Functions ---
def parse_ios_version(output):
    """Parses Cisco IOS version from 'show version' output."""
    match = re.search(r"Version\s+([\d\w\.]+),", output)
    if match:
        return match.group(1).strip()
    return "N/A"

def parse_serial_number(output):
    """Parses serial number (Processor board ID) from 'show version' output."""
    match = re.search(r"Processor board ID\s+(\S+)", output)
    if match:
        return match.group(1).strip()
    match = re.search(r"Serial Number\s+:\s+(\S+)", output) # For devices that use this format
    if match:
        return match.group(1).strip()
    return "N/A"

def parse_interface_name(output, ip_address):
    """
    Parses the interface name from 'show ip interface brief | include <IP>' output.
    Assumes the IP address is directly included in the command for filtering.
    """
    # Escaping IP address for regex to handle dots correctly
    ip_regex = re.escape(ip_address)
    # Regex to find the interface name (first word) followed by the IP address on the same line
    # ^(\S+)\s+: matches interface at start of line
    # .*?: non-greedy match for anything between interface and IP
    # \s+UP\s+(?:up|down): to confirm the line is likely for an active interface
    match = re.search(r"^(\S+)\s+"+ ip_regex + r"\s+(?:YES|NO)\s+(?:manual|NVRAM|unset)\s+(up|down)\s+(up|down)", output, re.MULTILINE | re.IGNORECASE)
    if match:
        return match.group(1).strip() # Capture the interface name
    return "N/A"

def parse_mac_from_show_interface(output):
    """
    Parses the MAC address from 'show interface <interface>' output.
    Looks for "address is AAAA.BBBB.CCCC (bia AAAA.BBBB.CCCC)" or similar patterns.
    """
    # Regex to find "address is" followed by the MAC (4.4.4 format)
    match = re.search(r"address is\s+([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})", output)
    if match:
        return match.group(1).upper()
    return "N/A"

if __name__ == "__main__":
    input_devices_csv = "devices.csv"

    # Define the commands you want to run on the switches.
    # {IP_ADDR_VAR} will be replaced by the device's IP address.
    # {INTERFACE_NAME_VAR} will be dynamically determined and replaced by the script.
    # The LAST command's output will populate the 'Last Command Output' column in the CSV.
    switch_commands = [
        "terminal length 0",
        "show version", # Needed for IOS Version, Serial Number
        "show ip interface brief | include {IP_ADDR_VAR}", # Essential for finding the interface name
        # "show interface {INTERFACE_NAME_VAR}" will be run dynamically after interface discovery
        "show interface status", # Example of another command. This output will be 'Last Command Output'
        "terminal no length"
    ]

    # --- Dummy CSV File Creation for Demonstration (REMOVE IN PRODUCTION) ---
    # This block creates a sample devices.csv if it doesn't exist.
    if not os.path.exists(input_devices_csv):
        print(f"Creating a dummy '{input_devices_csv}' for demonstration purposes.")
        dummy_data = [
            {'Hostname': 'TestSwitch1', 'IP Address': '192.168.1.10'}, # Replace with real IPs
            {'Hostname': 'TestSwitch2', 'IP Address': '192.168.1.11'},
            {'Hostname': 'TestRouter3', 'IP Address': '10.0.0.1'},
            {'Hostname': 'TestSwitch4', 'IP Address': '172.16.0.254'}
        ]
        with open(input_devices_csv, mode='w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=['Hostname', 'IP Address'])
            writer.writeheader()
            writer.writerows(dummy_data)
    # --- End of Dummy CSV Creation ---

    run_commands_and_extract_info(input_devices_csv, switch_commands)
    print("\nScript execution finished. Check the main log file, error_output.txt, and the processed_devices_*.csv for details.")