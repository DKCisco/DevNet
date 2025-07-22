import netmiko
import getpass
import os

# --- User Inputs ---
username = input("Enter SSH username: ")
password = getpass.getpass("Enter SSH password: ") # getpass hides input for security

# --- File Paths ---
ip_list_file = "2960x_ips.txt"       # File containing IP addresses of 2960X switches
config_commands_file = "2960x_config.txt" # File containing configuration commands for 2960X
log_file = "2960x_deployment_log.txt"
error_log_file = "2960x_ssh_error_log.txt"

# --- Load Configuration Commands ---
def load_config_commands(filepath):
    """Loads configuration commands from a text file, ignoring comments."""
    try:
        with open(filepath, 'r') as f:
            # Filter out empty lines and lines starting with '#' (comments)
            commands = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
            if not commands:
                print(f"Warning: Configuration commands file '{filepath}' is empty or only contains comments. No commands will be applied.")
            return commands
    except FileNotFoundError:
        print(f"Error: Configuration commands file '{filepath}' not found. Please create it.")
        return []

config_commands = load_config_commands(config_commands_file)

# --- Main Logic ---
def main():
    if not config_commands:
        print("Script cannot proceed without configuration commands. Exiting.")
        return

    # Initialize log files (clear previous content if they exist)
    with open(log_file, "w") as log_output:
        log_output.write("--- Cisco 2960X Configuration Deployment Log ---\n\n")

    with open(error_log_file, "w") as error_output:
        error_output.write("--- Cisco 2960X SSH Error Log ---\n\n")

    try:
        with open(ip_list_file, "r") as f:
            ip_addresses = [ip.strip() for ip in f if ip.strip()]
            if not ip_addresses:
                print(f"Error: IP list file '{ip_list_file}' is empty. No devices to process.")
                return
    except FileNotFoundError:
        print(f"Error: IP list file '{ip_list_file}' not found. Please create it.")
        return

    print(f"Starting configuration deployment to {len(ip_addresses)} devices from '{ip_list_file}'...")

    for ip_address in ip_addresses:
        print(f"\n--- Processing IP: {ip_address} ---")
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

                # Push configuration commands
                print(f"  Pushing configuration to {ip_address}...")
                output = net_connect.send_config_set(config_commands)
                log_output.write(f"  Configuration Commands Sent:\n")
                for cmd in config_commands:
                    log_output.write(f"    {cmd}\n")
                log_output.write(f"  Configuration Output:\n{output}\n")
                log_output.write(f"  Status: Configuration applied successfully.\n")
                print(f"  Configuration applied successfully to {ip_address}")

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