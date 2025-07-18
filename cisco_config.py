import paramiko
import getpass
import os
import datetime
import subprocess
import csv
import re
import time

# --- Paramiko Helper Functions (Crucial for interaction) ---
def read_until_prompt(channel, prompt="#", timeout=5):
    """Reads all data from the channel until the prompt is found."""
    output = ""
    start_time = time.time()
    while not output.strip().endswith(prompt) and (time.time() - start_time < timeout):
        if channel.recv_ready():
            output += channel.recv(65535).decode('utf-8', errors='ignore')
        else:
            time.sleep(0.05)

    cleaned_output = output.strip()
    if cleaned_output.endswith(prompt):
        cleaned_output = cleaned_output[:-len(prompt)].strip()
    return cleaned_output

def send_command_and_read(channel, command, prompt="#", timeout=5):
    """Sends a command and reads output until the prompt is found."""
    channel.send(command + "\n")
    time.sleep(0.1)
    initial_read = ""
    if channel.recv_ready():
        initial_read = channel.recv(65535).decode('utf-8', errors='ignore')

    output = read_until_prompt(channel, prompt, timeout)

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
        enable_password = password

    devices_data = []

    try:
        with open(input_csv_file, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            if 'Hostname' not in reader.fieldnames or 'IP Address' not in reader.fieldnames:
                raise ValueError("Input CSV must contain 'Hostname' and 'IP Address' columns.")
            for row in reader:
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

            device['Status'] = 'Pending'
            device['Error Message'] = ''
            device['IOS Version'] = ''
            device['Serial Number'] = ''
            device['Interface Name'] = ''
            device['Base MAC Address'] = ''
            device['Last Command Output'] = ''


            f_main_log.write(f"--- Processing Device: {hostname} ({ip_address}) ---\n")
            print(f"--- Processing Device: {hostname} ({ip_address}) ---")

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

            f_main_log.write(f"Attempting SSH connection to {ip_address} using Paramiko...\n")
            print(f"Attempting SSH connection to {ip_address} using Paramiko...")
            client = None
            channel = None
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(hostname=ip_address, username=username, password=password, timeout=10, look_for_keys=False, allow_agent=False)

                channel = client.invoke_shell()
                time.sleep(0.5)
                initial_output = read_until_prompt(channel, prompt='>|#')

                f_main_log.write(f"Initial shell output:\n{initial_output}\n")
                print(f"Successfully connected to {hostname} ({ip_address})")

                if not initial_output.strip().endswith('#'):
                    f_main_log.write("Attempting to enter enable mode.\n")
                    print("Attempting to enter enable mode.")
                    send_command_and_read(channel, "enable", prompt='Password:')
                    enable_output = send_command_and_read(channel, enable_password, prompt='#')
                    if not enable_output.strip().endswith('#'):
                        raise paramiko.SSHException("Failed to enter enable mode. Check enable password.")
                    f_main_log.write("Entered enable mode.\n")
                    print("Entered enable mode.")

                send_command_and_read(channel, "terminal length 0", prompt='#')
                f_main_log.write("Disabled pagination (terminal length 0).\n")
                print("Disabled pagination (terminal length 0).")


                show_version_output = ""
                show_ip_int_brief_output_for_ip = ""
                show_ip_arp_output_for_ip = ""
                last_command_output = ""

                # Execute static commands and capture relevant output
                for i, command_template in enumerate(commands):
                    command_to_execute = command_template

                    if "{IP_ADDR_VAR}" in command_template:
                        command_to_execute = command_template.replace("{IP_ADDR_VAR}", ip_address)
                    elif "{INTERFACE_NAME_VAR}" in command_template:
                         # This command should never be in the static list, as it's dynamic
                        continue

                    f_main_log.write(f"Executing command: {command_to_execute}\n")
                    print(f"Executing command: {command_to_execute}")
                    output = send_command_and_read(channel, command_to_execute, prompt='#')
                    f_main_log.write(f"Command Output:\n{output}\n")
                    print(f"Command Output:\n{output}")

                    if "show version" in command_to_execute.lower() and "terminal length" not in command_to_execute.lower():
                        show_version_output = output
                    if "show ip interface brief" in command_to_execute.lower() and ip_address in command_to_execute:
                        show_ip_int_brief_output_for_ip = output
                    if "show ip arp" in command_to_execute.lower() and ip_address in command_to_execute:
                        show_ip_arp_output_for_ip = output

                    if i == len(commands) - 1:
                        last_command_output = output.strip()

                # --- Interface Discovery and Loopback Fallback Logic ---
                initial_discovered_interface = "N/A"

                # 1. Try 'show ip int brief | include {IP}'
                if show_ip_int_brief_output_for_ip:
                    initial_discovered_interface = parse_interface_name(show_ip_int_brief_output_for_ip, ip_address)

                # 2. If that fails, try 'show ip arp | include {IP}'
                if initial_discovered_interface == "N/A" and show_ip_arp_output_for_ip:
                    f_main_log.write(f"Interface not found via 'show ip int brief' for {ip_address}. Attempting 'show ip arp'.\n")
                    print(f"Interface not found via 'show ip int brief' for {ip_address}. Attempting 'show ip arp'.")
                    initial_discovered_interface = parse_interface_from_arp(show_ip_arp_output_for_ip, ip_address)
                    if initial_discovered_interface != "N/A":
                        f_main_log.write(f"Interface '{initial_discovered_interface}' found via 'show ip arp' for {ip_address}.\n")
                        print(f"Interface '{initial_discovered_interface}' found via 'show ip arp' for {ip_address}.")
                    else:
                        f_main_log.write(f"Interface not found via 'show ip arp' either for {ip_address}.\n")
                        print(f"Interface not found via 'show ip arp' either for {ip_address}.")

                device['Interface Name'] = initial_discovered_interface # Tentative assignment

                # 3. Check for Loopback and find a suitable physical interface
                if device['Interface Name'].lower().startswith("loopback") and device['Interface Name'] != "N/A":
                    f_main_log.write(f"Loopback interface '{device['Interface Name']}' detected for {ip_address}. Searching for a physical interface with an IP.\n")
                    print(f"Loopback interface '{device['Interface Name']}' detected for {ip_address}. Searching for a physical interface with an IP.")

                    # Execute full 'show ip interface brief' to get all interfaces
                    full_ip_int_brief_output = send_command_and_read(channel, "show ip interface brief", prompt='#')
                    f_main_log.write(f"Full 'show ip interface brief' output for physical interface search:\n{full_ip_int_brief_output}\n")

                    physical_interface = find_non_loopback_active_interface(full_ip_int_brief_output)

                    if physical_interface != "N/A":
                        device['Interface Name'] = physical_interface
                        f_main_log.write(f"Found suitable physical interface '{physical_interface}' for MAC retrieval.\n")
                        print(f"Found suitable physical interface '{physical_interface}' for MAC retrieval.")
                    else:
                        device['Interface Name'] = "N/A - Loopback detected, no suitable physical interface found"
                        f_main_log.write(f"No suitable physical interface found for {ip_address} after loopback detection.\n")
                        print(f"No suitable physical interface found for {ip_address} after loopback detection.")

                # --- MAC Address Retrieval (based on final 'Interface Name') ---
                if device['Interface Name'] and "N/A" not in device['Interface Name'] and "Failed" not in device['Interface Name']:
                    f_main_log.write(f"Dynamically executing: show interface {device['Interface Name']}\n")
                    print(f"Dynamically executing: show interface {device['Interface Name']}")
                    mac_detail_output = send_command_and_read(channel, f"show interface {device['Interface Name']}", prompt='#')
                    f_main_log.write(f"Command Output (show interface {device['Interface Name']}):\n{mac_detail_output}\n")
                    print(f"Command Output (show interface {device['Interface Name']}):\n{mac_detail_output}")
                    device['Base MAC Address'] = parse_mac_from_show_interface(mac_detail_output)
                else:
                    f_main_log.write(f"No valid interface name to retrieve MAC for {ip_address}.\n")
                    print(f"No valid interface name to retrieve MAC for {ip_address}.")
                    device['Base MAC Address'] = "N/A - Interface Unknown"

                send_command_and_read(channel, "terminal no length", prompt='#')
                f_main_log.write("Reset terminal length.\n")

                device['Status'] = 'Success'
                device['Last Command Output'] = last_command_output

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
    match = re.search(r"Version\s+([\d\w\.]+),", output, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "N/A"

def parse_serial_number(output):
    """Parses serial number (Processor board ID) from 'show version' output."""
    match = re.search(r"Processor board ID\s+(\S+)", output, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r"Serial Number\s+:\s+(\S+)", output, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "N/A"

def parse_interface_name(output, ip_address):
    """
    Parses the interface name from 'show ip interface brief | include <IP>' output.
    """
    ip_regex = re.escape(ip_address)
    # Match interface at start, followed by IP, then typical status
    match = re.search(r"^(\S+)\s+" + ip_regex + r"\s+(?:YES|NO|unassigned)\s+(?:manual|NVRAM|unset)\s+(up|down|administratively down)\s+(up|down)", output, re.MULTILINE | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "N/A"

def parse_interface_from_arp(output, ip_address):
    """
    Parses the interface name from 'show ip arp | include <IP>' output.
    """
    ip_regex = re.escape(ip_address)
    # Match the IP, then capture the last word (interface name) on the line
    # (?:Protocol\s+)?(Internet|ARPA)\s+ is optional capture for protocol if header is sometimes present
    # \s+\S+\s+\S+\s+\S+\s+ are placeholders for Age, Hardware Addr, Type
    match = re.search(r"\s+" + ip_regex + r"\s+\S+\s+\S+\s+\S+\s+(\S+)$", output, re.MULTILINE | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "N/A"

def find_non_loopback_active_interface(output):
    """
    Parses 'show ip interface brief' output to find the first non-loopback,
    IP-assigned, up/up interface.
    """
    lines = output.splitlines()
    # Skip header lines
    data_lines = [line for line in lines if not line.strip().startswith(('Interface', 'Protocol')) and line.strip()]

    for line in data_lines:
        parts = line.split()
        if len(parts) >= 6: # Expect at least Interface, IP-Address, OK?, Method, Status, Protocol
            interface_name = parts[0]
            ip_address = parts[1]
            status_line = parts[4].lower() # e.g., 'up' or 'down'
            protocol_status = parts[5].lower() # e.g., 'up' or 'down'

            # Check if it's not a loopback, has an IP, and is up/up
            if not interface_name.lower().startswith("loopback") and \
               ip_address != "unassigned" and \
               status_line == "up" and \
               protocol_status == "up":
                return interface_name.strip()
    return "N/A"


def parse_mac_from_show_interface(output):
    """
    Parses the MAC address from 'show interface <interface>' output.
    """
    match = re.search(r"address is\s+([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})", output, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return "N/A"

if __name__ == "__main__":
    input_devices_csv = "devices.csv"

    switch_commands = [
        "terminal length 0",
        "show version",
        "show ip interface brief | include {IP_ADDR_VAR}", # Primary method for interface discovery
        "show ip arp | include {IP_ADDR_VAR}",             # Fallback method for interface discovery
        "show interface status", # Example: This output will be saved as 'Last Command Output'
        "terminal no length"
    ]

    run_commands_and_extract_info(input_devices_csv, switch_commands)
    print("\nScript execution finished. Check the main log file, error_output.txt, and the processed_devices_*.csv for details.")