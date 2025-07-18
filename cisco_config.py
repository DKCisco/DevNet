import netmiko
import getpass
import os
import datetime
import subprocess
import csv

def run_commands_on_cisco(ip_list_file, commands):
    """
    Connects to Cisco switches via SSH, runs commands, and logs results.
    Logs all output to a main log file, errors to error_output.txt,
    and the last command's output (intended as show command) to a CSV file.

    Args:
        ip_list_file (str): Path to a text file containing IP addresses, one per line.
        commands (list): A list of commands to execute on the switches.
    """

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    main_log_file = f"cisco_ssh_main_log_{timestamp}.txt"
    error_log_file = "error_output.txt" # Single file for all errors
    csv_output_file = "ssh_show_output.csv" # Single CSV file for show command results

    print(f"Logging main output to: {main_log_file}")
    print(f"Logging errors to: {error_log_file}")
    print(f"Logging show command output to CSV: {csv_output_file}\n")

    username = input("Enter SSH username: ")
    password = getpass.getpass("Enter SSH password: ")

    try:
        with open(ip_list_file, 'r') as f_ip:
            ip_addresses = [line.strip() for line in f_ip if line.strip()]
    except FileNotFoundError:
        print(f"Error: IP list file '{ip_list_file}' not found.")
        with open(error_log_file, 'a') as f_error:
            f_error.write(f"{datetime.datetime.now()}: Error: IP list file '{ip_list_file}' not found.\n")
        return

    # Prepare CSV header - Assuming the first column is IP, and then the output of the last command
    csv_header_written = os.path.exists(csv_output_file) # Check if file exists to avoid writing header multiple times
    if not csv_header_written:
        with open(csv_output_file, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['IP Address', 'Show Command Output']) # Header row

    with open(main_log_file, 'a') as f_main_log, open(error_log_file, 'a') as f_error_log, \
         open(csv_output_file, 'a', newline='') as f_csv_output:

        csv_writer = csv.writer(f_csv_output)

        for ip_address in ip_addresses:
            f_main_log.write(f"--- Processing IP: {ip_address} ---\n")
            print(f"--- Processing IP: {ip_address} ---")

            # 1. Ping the IP address
            f_main_log.write(f"Attempting to ping {ip_address}...\n")
            print(f"Attempting to ping {ip_address}...")
            try:
                # Use platform-independent ping command
                if os.name == 'nt':  # For Windows
                    ping_command = ['ping', '-n', '1', ip_address]
                else:  # For Linux/macOS
                    ping_command = ['ping', '-c', '1', ip_address]

                ping_output = subprocess.run(
                    ping_command, capture_output=True, text=True, timeout=10
                )
                f_main_log.write(f"Ping Result:\n{ping_output.stdout}\n{ping_output.stderr}\n")
                print(f"Ping Result:\n{ping_output.stdout}")

                if ping_output.returncode != 0:
                    f_main_log.write(f"Ping to {ip_address} failed. Skipping SSH attempt.\n\n")
                    print(f"Ping to {ip_address} failed. Skipping SSH attempt.\n")
                    f_error_log.write(f"{datetime.datetime.now()}: Ping failed for {ip_address}\n")
                    continue

            except subprocess.TimeoutExpired:
                f_main_log.write(f"Ping to {ip_address} timed out. Skipping SSH attempt.\n\n")
                print(f"Ping to {ip_address} timed out. Skipping SSH attempt.\n")
                f_error_log.write(f"{datetime.datetime.now()}: Ping timed out for {ip_address}\n")
                continue
            except Exception as e:
                f_main_log.write(f"Error during ping to {ip_address}: {e}. Skipping SSH attempt.\n\n")
                print(f"Error during ping to {ip_address}: {e}. Skipping SSH attempt.\n")
                f_error_log.write(f"{datetime.datetime.now()}: Ping error for {ip_address}: {e}\n")
                continue

            # 2. Attempt SSH connection
            f_main_log.write(f"Attempting SSH connection to {ip_address}...\n")
            print(f"Attempting SSH connection to {ip_address}...")
            device = {
                "device_type": "cisco_ios",
                "host": ip_address,
                "username": username,
                "password": password,
                "secret": password,  # For privilege mode if needed
            }

            last_command_output = "" # To store the output of the last command for CSV

            try:
                with netmiko.ConnectHandler(**device) as net_connect:
                    f_main_log.write(f"Successfully connected to {ip_address}\n")
                    print(f"Successfully connected to {ip_address}")

                    # Enter enable mode if not already
                    if not net_connect.check_enable_mode():
                        net_connect.enable()
                        f_main_log.write("Entered enable mode.\n")
                        print("Entered enable mode.")

                    for i, command in enumerate(commands):
                        f_main_log.write(f"Executing command: {command}\n")
                        print(f"Executing command: {command}")
                        output = net_connect.send_command(command)
                        f_main_log.write(f"Command Output:\n{output}\n")
                        print(f"Command Output:\n{output}")

                        # If this is the last command, store its output for CSV
                        if i == len(commands) - 1:
                            last_command_output = output.strip() # Remove leading/trailing whitespace

                    f_main_log.write(f"--- Finished commands for {ip_address} ---\n\n")
                    print(f"--- Finished commands for {ip_address} ---\n")

                    # Write to CSV after successful session
                    csv_writer.writerow([ip_address, last_command_output])

            except netmiko.NetmikoTimeoutException:
                f_main_log.write(f"SSH connection to {ip_address} timed out.\n\n")
                print(f"SSH connection to {ip_address} timed out.\n")
                f_error_log.write(f"{datetime.datetime.now()}: SSH timeout for {ip_address}\n")
            except netmiko.NetmikoAuthenticationException:
                f_main_log.write(f"SSH authentication failed for {ip_address}.\n\n")
                print(f"SSH authentication failed for {ip_address}.\n")
                f_error_log.write(f"{datetime.datetime.now()}: SSH authentication failed for {ip_address}\n")
            except Exception as e:
                f_main_log.write(f"An unexpected SSH error occurred for {ip_address}: {e}\n\n")
                print(f"An unexpected SSH error occurred for {ip_address}: {e}\n")
                f_error_log.write(f"{datetime.datetime.now()}: Unexpected SSH error for {ip_address}: {e}\n")

if __name__ == "__main__":
    ip_file = "ip_addresses.txt" # This must be created by the user

    # Define the commands you want to run on the switches.
    # The LAST command in this list will be captured for the CSV file.
    switch_commands = [
        "terminal length 0", # Important: Prevents pagination for full output
        "show version | include Cisco IOS Software",
        "show ip interface brief",
        "show mac address-table count", # This will be the output saved to CSV
        "terminal no length" # Reset terminal length
    ]
    # Ensure your last command provides data suitable for a single cell in a CSV.
    # If your show command output is multi-line and you want it in one cell,
    # CSV writers handle this by default by enclosing it in quotes.

    # Dummy file creation for demonstration - REMOVE IN PRODUCTION
    if not os.path.exists(ip_file):
        print(f"Creating a dummy '{ip_file}' for demonstration purposes.")
        with open(ip_file, "w") as f:
            f.write("192.168.1.10\n") # Replace with your actual switch IPs
            f.write("192.168.1.11\n") # This one will fail if not reachable/auth issues
            f.write("10.0.0.1\n")
            f.write("172.16.0.254\n")
    # End of dummy file creation

    run_commands_on_cisco(ip_file, switch_commands)
    print("\nScript execution finished. Check the main log file, error_output.txt, and ssh_show_output.csv for details.")