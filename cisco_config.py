import paramiko # Changed from netmiko
import getpass
import os
import datetime
import subprocess
import csv
import re # For regular expressions to parse show command output
import time # For delays in paramiko interaction

# --- Paramiko Helper Functions (Crucial for interaction) ---
def read_until_prompt(channel, prompt="#", timeout=5):
    """Reads all data from the channel until the prompt is found."""
    output = ""
    start_time = time.time()
    while not output.strip().endswith(prompt) and (time.time() - start_time < timeout):
        if channel.recv_ready():
            output += channel.recv(65535).decode('utf-8', errors='ignore') # Read larger chunks
        else:
            time.sleep(0.05) # Small delay to prevent busy-waiting

    # Clean up output: remove prompt, and potentially the echoed command
    # This part is simplified and might need tuning for very complex prompts/echoes
    cleaned_output = output.strip()
    if cleaned_output.endswith(prompt):
        cleaned_output = cleaned_output[:-len(prompt)].strip()
    return cleaned_output

def send_command_and_read(channel, command, prompt="#", timeout=5):
    """Sends a command and reads output until the prompt is found."""
    channel.send(command + "\n")
    # Read once to clear the echoed command, then read for actual output + prompt
    time.sleep(0.1) # Give time for echo
    initial_read = ""
    if channel.recv_ready():
        initial_read = channel.recv(65535).decode('utf-8', errors='ignore')

    output = read_until_prompt(channel, prompt, timeout)

    # Attempt to remove the echoed command from the output.
    # This can be tricky; a more robust solution might check for the prompt before sending.
    if initial_read.strip().endswith(command):
        output = output.replace(initial_read.strip(), "", 1).strip()
    elif output.startswith(command):
        output = output.replace(command, "", 1).strip()

    return output


def run_commands_and_extract_info(input_csv_file, commands):
    """
    Connects to Cisco switches via SSH, runs commands, extracts specific info,
    and logs results to CSV and text files using Paramiko.

    Args:
        input_csv_file (str): Path to a CSV file with 'Hostname' and 'IP Address' columns.
        commands (list): A list of commands to execute on the switches.
                         Can contain {IP_ADDR_VAR} for the device's own IP.
                         {INTERFACE_NAME_VAR} will be dynamically replaced after discovery.
    """

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    main_log_file = f"cisco_ssh_main_log_{timestamp}.txt"
    error_log_file = "error_output.txt"
    output_csv_file = f"processed_devices_{timestamp}.csv"

    print(f"Logging main output to: {main_log_file}")
    print(f"Logging errors to: {error_log_file}")
    print(f"Logging processed data to CSV: {output_csv_file}\n")

    username = input("Enter SSH username: ")
    password = getpass.getpass("Enter SSH password: ")
    enable_password = getpass.getpass("Enter Enable password (if different from SSH password, else press Enter): ")
    if not enable_password:
        enable_password = password # Use SSH password as enable password if not provided

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
                row['Interface Name'] = ''
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

            # 2. Attempt SSH connection using Paramiko
            f_main_log.write(f"Attempting SSH connection to {ip_address} using Paramiko...\n")
            print(f"Attempting SSH connection to {ip_address} using Paramiko...")
            client = None
            channel = None
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # Auto add host keys
                client.connect(hostname=ip_address, username=username, password=password, timeout=10)

                channel = client.invoke_shell()
                time.sleep(0.5) # Give some time for the shell to open and banner to appear
                initial_output = read_until_prompt(channel, prompt='>|#') # Read initial prompt

                f_main_log.write(f"Initial shell output:\n{initial_output}\n")
                print(f"Successfully connected to {hostname} ({ip_address})")

                # Check if already in enable mode, if not, try to enter
                if not initial_output.strip().endswith('#'):
                    f_main_log.write("Attempting to enter enable mode.\n")
                    print("Attempting to enter enable mode.")
                    send_command_and_read(channel, "enable", prompt='Password:') # Send enable, expect password prompt
                    enable_output = send_command_and_read(channel, enable_password, prompt='#') # Send enable password, expect enable prompt
                    if not enable_output.strip().endswith('#'):
                        raise paramiko.SSHException("Failed to enter enable mode. Check enable password.")
                    f_main_log.write("Entered enable mode.\n")
                    print("Entered enable mode.")

                # Disable pagination
                send_command_and_read(channel, "terminal length 0", prompt='#')
                f_main_log.write("Disabled pagination (terminal length 0).\n")
                print("Disabled pagination (terminal length 0).")


                show_version_output = ""
                show_ip_int_brief_output_for_ip = ""
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
                    output = send_command_and_read(channel, command_to_execute, prompt='#')
                    f_main_log.write(f"Command Output:\n{output}\n")
                    print(f"Command Output:\n{output}")

                    # Store specific command outputs for parsing
                    if "show version" in command_to_execute.lower() and "terminal length" not in command_to_execute.lower():
                        show_version_output = output
                    if "show ip interface brief" in command_to_execute.lower() and ip_address in command_to_execute:
                        show_ip_int_brief_output_for_ip = output

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
                if extracted_interface and extracted_interface != "N/A": # Ensure it's a valid interface
                    # Dynamically run 'show interface <interface_name>' to get MAC
                    f_main_log.write(f"Dynamically executing: show interface {extracted_interface}\n")
                    print(f"Dynamically executing: show interface {extracted_interface}")
                    mac_detail_output = send_command_and_read(channel, f"show interface {extracted_interface}", prompt='#')
                    f_main_log.write(f"Command Output (show interface {extracted_interface}):\n{mac_detail_output}\n")
                    print(f"Command Output (show interface {extracted_interface}):\n{mac_detail_output}")
                    device['Base MAC Address'] = parse_mac_from_show_interface(mac_detail_output)
                else:
                    f_main_log.write(f"Could not determine primary interface for {ip_address}. Skipping MAC address retrieval.\n")
                    print(f"Could not determine primary interface for {ip_address}. Skipping MAC address retrieval.")
                    device['Base MAC Address'] = "N/A - Interface Not Found"

                # Reset terminal length (optional but good practice)
                send_command_and_read(channel, "terminal no length", prompt='#')
                f_main_log.write("Reset terminal length.\n")


                device['Status'] = 'Success'
                device['Last Command Output'] = last_command_output # Assign the last command's output

            except paramiko.AuthenticationException:
                device['Status'] = 'Authentication Failed'
                device['Error Message'] = "SSH authentication failed (username/password/enable password)."
                f_main_log.write(f"SSH authentication failed for {ip_address}.\n\n")
                print(f"SSH authentication failed for {ip_address}.\n")
                f_error_log.write(f"{datetime.datetime.now()}: SSH authentication failed for {hostname} ({ip_address})\n")
            except paramiko.SSHException as ssh_err:
                device['Status'] = 'SSH Error'
                device['Error Message'] = f"SSH error: {ssh_err}"
                f_main_log.write(f"An SSH error occurred for {ip_address}: {ssh_err}\n\n")
                print(f"An SSH error occurred for {ip_address}: {ssh_err}\n")
                f_error_log.write(f"{datetime.datetime.now()}: SSH error for {hostname} ({ip_address}): {ssh_err}\n")
            except Exception as e:
                device['Status'] = 'General Error'
                device['Error Message'] = f"An unexpected error occurred during SSH session: {e}"
                f_main_log.write(f"An unexpected error occurred for {ip_address}: {e}\n\n")
                print(f"An unexpected error occurred for {ip_address}: {e}\n")
                f_error_log.write(f"{datetime.datetime.now()}: General error for {hostname} ({ip_address}): {e}\n")
            finally:
                if channel:
                    channel.close()
                if client:
                    client.close()

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

# --- Parsing Functions (remain mostly the same, adjusted for potential output differences) ---
def parse_ios_version(output):
    """Parses Cisco IOS version from 'show version' output."""
    match = re.search(r"Version\s+([\d\w\.]+),", output, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "N/A"

def parse_serial_number(output):
    """Parses serial number (Processor board ID) from 'show version' output."""
    match = re.search(r"Processor board ID\s+(\S+)", output, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r"Serial Number\s+:\s+(\S+)", output, re.IGNORECASE) # For devices that use this format
    if match:
        return match.group(1).strip()
    return "N/A"

def parse_interface_name(output, ip_address):
    """
    Parses the interface name from 'show ip interface brief | include <IP>' output.
    Assumes the IP address is directly included in the command for filtering.
    """
    ip_regex = re.escape(ip_address)
    # This regex is made more robust to handle various spaces and status columns.
    # It looks for interface name at the start of the line, followed by the IP.
    match = re.search(r"^(\S+)\s+" + ip_regex + r"\s+(?:YES|NO|unassigned)\s+(?:manual|NVRAM|unset)\s+(up|down|administratively down)\s+(up|down)", output, re.MULTILINE | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "N/A"

def parse_mac_from_show_interface(output):
    """
    Parses the MAC address from 'show interface <interface>' output.
    Looks for "address is AAAA.BBBB.CCCC (bia AAAA.BBBB.CCCC)" or similar patterns.
    """
    # Look for "address is" followed by the MAC (4.4.4 format)
    match = re.search(r"address is\s+([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})", output, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return "N/A"

if __name__ == "__main__":
    input_devices_csv = "devices.csv"

    # Define the commands you want to run on the switches.
    # {IP_ADDR_VAR} will be replaced by the device's IP address.
    # {INTERFACE_NAME_VAR} will be dynamically determined and replaced by the script for the 'show interface' command.
    # The LAST command's output will populate the 'Last Command Output' column in the CSV.
    switch_commands = [
        "terminal length 0", # Ensure no pagination
        "show version",      # For IOS Version, Serial Number
        "show ip interface brief | include {IP_ADDR_VAR}", # For finding the interface name for the IP
        # Note: "show interface {INTERFACE_NAME_VAR}" is executed dynamically by the script after interface discovery
        "show interface status", # Example: This output will be saved as 'Last Command Output'
        "terminal no length" # Reset pagination
    ]

    run_commands_and_extract_info(input_devices_csv, switch_commands)
    print("\nScript execution finished. Check the main log file, error_output.txt, and the processed_devices_*.csv for details.")