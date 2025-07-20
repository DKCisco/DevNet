import netmiko
import getpass
import re
import os

# --- User Inputs ---
username = input("Enter SSH username: ")
password = getpass.getpass("Enter SSH password: ") # getpass hides input for security

# --- File Paths ---
ip_list_file = "device_ips.txt"
acl_2960x_isr_file = "acl_2960x_isr.txt"  # ACL for 2960X and ISR4331
acl_9200_file = "acl_9200.txt"            # ACL for Catalyst 9200
log_file = "network_device_log.txt"
error_log_file = "ssh_error_log.txt"

# --- Load ACLs ---
def load_acl_from_file(filepath):
    """Loads ACL commands from a text file."""
    try:
        with open(filepath, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    except FileNotFoundError:
        print(f"Error: ACL file '{filepath}' not found. Please create it.")
        return []

acl_2960x_isr_commands = load_acl_from_file(acl_2960x_isr_file)
acl_9200_commands = load_acl_from_file(acl_9200_file)

# --- Main Logic ---
def main():
    if not acl_2960x_isr_commands:
        print(f"Warning: No ACL commands loaded from '{acl_2960x_isr_file}'. ACLs for 2960X/ISR will not be applied.")
    if not acl_9200_commands:
        print(f"Warning: No ACL commands loaded from '{acl_9200_file}'. ACLs for 9200 will not be applied.")

    # Initialize log files
    with open(log_file, "w") as log_output:
        log_output.write("--- Network Device Connection and Configuration Log ---\n\n")

    with open(error_log_file, "w") as error_output:
        error_output.write("--- SSH Connection Error Log ---\n\n")

    try:
        with open(ip_list_file, "r") as f:
            ip_addresses = [ip.strip() for ip in f if ip.strip()]
    except FileNotFoundError:
        print(f"Error: IP list file '{ip_list_file}' not found. Please create it.")
        return

    for ip_address in ip_addresses:
        print(f"Processing IP: {ip_address}")
        with open(log_file, "a") as log_output, open(error_log_file, "a") as error_output:
            log_output.write(f"Attempting connection to IP: {ip_address}\n")

            device_info = {
                'device_type': 'cisco_ios', # Netmiko device type for Cisco IOS
                'host': ip_address,
                'username': username,
                'password': password,
            }

            net_connect = None # Initialize net_connect to None

            try:
                net_connect = netmiko.ConnectHandler(**device_info)
                log_output.write(f"Successfully connected to {ip_address}\n")
                print(f"  Connected to {ip_address}")

                # Get hostname
                hostname_output = net_connect.send_command('sh run | i hostname')
                log_output.write(f"  Hostname: {hostname_output.strip()}\n")
                print(f"  Hostname: {hostname_output.strip()}")

                # Get inventory (model information)
                inventory_output = net_connect.send_command('sh inv')
                log_output.write(f"  Inventory:\n{inventory_output}\n")
                print(f"  Retrieved inventory for {ip_address}")

                device_model = "Unknown"
                acl_applied = "None"

                # Check device model and apply ACL accordingly
                if re.search(r'WS-C2960X', inventory_output, re.IGNORECASE):
                    device_model = "Cisco Catalyst 2960X"
                    log_output.write("  Detected Model: Cisco Catalyst 2960X\n")
                    if acl_2960x_isr_commands:
                        print(f"  Applying 2960X/ISR ACL to {ip_address}...")
                        output = net_connect.send_config_set(acl_2960x_isr_commands)
                        log_output.write(f"  ACL applied (2960X/ISR syntax):\n{output}\n")
                        print(f"  ACL applied to {ip_address}")
                        acl_applied = "2960X/ISR"
                    else:
                        log_output.write(f"  Skipping ACL application for 2960X. No commands loaded from '{acl_2960x_isr_file}'.\n")
                        print(f"  Skipping ACL for {ip_address} (2960X/ISR commands not loaded).")

                elif re.search(r'ISR4331', inventory_output, re.IGNORECASE):
                    device_model = "Cisco ISR 4331"
                    log_output.write("  Detected Model: Cisco ISR 4331\n")
                    if acl_2960x_isr_commands:
                        print(f"  Applying 2960X/ISR ACL to {ip_address}...")
                        output = net_connect.send_config_set(acl_2960x_isr_commands)
                        log_output.write(f"  ACL applied (2960X/ISR syntax):\n{output}\n")
                        print(f"  ACL applied to {ip_address}")
                        acl_applied = "2960X/ISR"
                    else:
                        log_output.write(f"  Skipping ACL application for ISR4331. No commands loaded from '{acl_2960x_isr_file}'.\n")
                        print(f"  Skipping ACL for {ip_address} (2960X/ISR commands not loaded).")

                elif re.search(r'C9200', inventory_output, re.IGNORECASE):
                    device_model = "Cisco Catalyst 9200"
                    log_output.write("  Detected Model: Cisco Catalyst 9200\n")
                    if acl_9200_commands:
                        print(f"  Applying 9200 ACL to {ip_address}...")
                        output = net_connect.send_config_set(acl_9200_commands)
                        log_output.write(f"  ACL applied (9200 syntax):\n{output}\n")
                        print(f"  ACL applied to {ip_address}")
                        acl_applied = "9200"
                    else:
                        log_output.write(f"  Skipping ACL application for C9200. No commands loaded from '{acl_9200_file}'.\n")
                        print(f"  Skipping ACL for {ip_address} (9200 commands not loaded).")
                else:
                    log_output.write("  Detected Model: Other/Unknown Cisco Device. No specific ACL applied.\n")
                    print(f"  Other/Unknown Cisco device: {ip_address}. No specific ACL applied.")

                log_output.write(f"  Final Status: Model={device_model}, ACL Applied={acl_applied}\n")

            except netmiko.NetmikoTimeoutException:
                log_output.write(f"  SSH Failure: Timeout when connecting to {ip_address}\n")
                error_output.write(f"{ip_address}: Timeout\n")
                print(f"  Timeout for {ip_address}, skipping.")
            except netmiko.NetmikoAuthenticationException:
                log_output.write(f"  SSH Failure: Authentication failed for {ip_address}\n")
                error_output.write(f"{ip_address}: Authentication Failed\n")
                print(f"  Authentication failed for {ip_address}, skipping.")
            except Exception as e:
                log_output.write(f"  SSH Failure: An unexpected error occurred with {ip_address}: {e}\n")
                error_output.write(f"{ip_address}: Unexpected Error - {e}\n")
                print(f"  Unexpected error with {ip_address}: {e}, skipping.")
            finally:
                if net_connect:
                    net_connect.disconnect()
                    log_output.write(f"  Disconnected from {ip_address}\n")
                log_output.write("-" * 40 + "\n\n")

    print(f"\nScript finished. Check '{log_file}' for details and '{error_log_file}' for SSH failures.")

if __name__ == "__main__":
    main()