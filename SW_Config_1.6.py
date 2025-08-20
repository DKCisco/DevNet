import paramiko
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import os
import config # Import the configuration file for cred variables

# --- File Paths ---
# These paths can remain here or be moved to config.py as well.
LOG_FILE_PATH = 'script_output.log'
IP_LIST_FILENAME = 'ip_addresses.txt'


# --- Helper Functions ---

def send_email(subject, body, sender, recipient, smtp_server, smtp_port):
    """
    Sends an email using the provided details.
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        print(f"Connecting to SMTP server {smtp_server}:{smtp_port}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        # If your SMTP server requires authentication, uncomment the next line
        # and replace with your email password or an app-specific password.
        # server.login(sender, "YOUR_EMAIL_PASSWORD")
        server.sendmail(sender, recipient, msg.as_string())
        server.quit()
        print(f"Email sent successfully to {recipient}")
    except Exception as e:
        print(f"Error sending email: {e}")

def log_output(ip, message, log_path):
    """
    Logs messages to a file with a timestamp and IP address.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] - {ip}\n{message}\n{'='*60}\n"
    with open(log_path, 'a') as log_file:
        log_file.write(log_entry)

# --- Core SSH Function ---

def ssh_to_switch(ip, username, password, commands):
    """
    Connects to a network switch via SSH and executes a list of commands.

    Args:
        ip (str): The IP address of the switch.
        username (str): The SSH username.
        password (str): The SSH password.
        commands (list): A list of commands to execute.

    Returns:
        tuple: A tuple containing (bool: success, str: output_message).
               - (True, output) on success.
               - (False, error_message) on failure.
    """
    output = ""
    try:
        print(f"Attempting to connect to {ip}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            ip,
            username=username,
            password=password,
            timeout=10,
            look_for_keys=False,
            allow_agent=False
        )
        print(f"Successfully connected to {ip}.")

        # Invoke an interactive shell
        channel = ssh.invoke_shell()
        time.sleep(2) # Wait for the shell to be ready

        # Read the initial banner and prompt
        initial_response = channel.recv(65535).decode('utf-8')
        output += f"--- Initial Response from {ip} ---\n{initial_response}\n"

        # This function waits for the command prompt before sending the next command
        def wait_for_prompt(prompt_regex=r"[\w.-]+[>#]\s*$"):
            buffer = ""
            while not re.search(prompt_regex, buffer.split('\n')[-1]):
                if channel.recv_ready():
                    buffer += channel.recv(1024).decode('utf-8')
                time.sleep(0.1)
            return buffer

        # Execute each command
        for command in commands:
            print(f"Sending command to {ip}: {command}")
            channel.send(command + "\n")
            # Wait for the command to execute and capture the output
            command_output = wait_for_prompt()
            output += f"\n--- Command: '{command}' ---\n{command_output}"
            time.sleep(1) # Small delay between commands

        print(f"Finished commands for {ip}.")
        channel.close()
        ssh.close()
        return (True, output)

    except paramiko.AuthenticationException:
        error_message = f"Authentication failed for {ip}. Please check username/password."
        print(error_message)
        return (False, error_message)
    except paramiko.SSHException as e:
        error_message = f"SSH connection error for {ip}: {e}"
        print(error_message)
        return (False, error_message)
    except Exception as e:
        error_message = f"An unexpected error occurred for {ip}: {e}"
        print(error_message)
        return (False, error_message)

# --- Main Execution ---

def main():
    """
    Main function to run the script using variables from the config.py file.
    """
    print("--- Network Switch Configuration Script (Automated) ---")

    # --- Define Commands ---
    # Note: 'enable' is sent first, then the other config commands.
    # The final '' (empty string) sends an Enter key press to confirm the save.
    commands_to_run = [
        'conf t',
        'do wr mem',
        '',
        'end'
    ]

    # --- Check for IP address file ---
    if not os.path.exists(IP_LIST_FILENAME):
        print(f"\nERROR: The file '{IP_LIST_FILENAME}' was not found.")
        print("Please create this file and add one IP address per line.")
        return

    with open(IP_LIST_FILENAME, 'r') as file:
        ip_addresses = [line.strip() for line in file.readlines() if line.strip()]

    if not ip_addresses:
        print(f"The file '{IP_LIST_FILENAME}' is empty. Nothing to do.")
        return

    print(f"\nFound {len(ip_addresses)} IP addresses to process.\n")

    # --- Process each IP address ---
    for ip in ip_addresses:
        print(f"--- Starting process for {ip} ---")
        # Use credentials from the imported config file
        success, result_output = ssh_to_switch(ip, config.SSH_USERNAME, config.SSH_PASSWORD, commands_to_run)

        # Log the full output regardless of success or failure
        log_output(ip, result_output, LOG_FILE_PATH)

        # Send email based on the result using settings from the config file
        if success:
            subject = f"SUCCESS: Configuration script completed for {ip}"
            body = (
                f"The configuration script has successfully run on the switch at {ip}.\n\n"
                f"Please see the attached log file '{LOG_FILE_PATH}' on the script server for detailed output."
            )
            send_email(subject, body, config.SENDER_EMAIL, config.RECIPIENT_EMAIL, config.SMTP_SERVER, config.SMTP_PORT)
        else:
            subject = f"ERROR: Configuration script failed for {ip}"
            body = (
                f"The configuration script encountered an error for the switch at {ip}.\n\n"
                f"Error Message:\n{result_output}\n\n"
                f"Please check the device and the log file '{LOG_FILE_PATH}' on the script server for more details."
            )
            send_email(subject, body, config.SENDER_EMAIL, config.RECIPIENT_EMAIL, config.SMTP_SERVER, config.SMTP_PORT)
        print("-" * 35)

    print("\n--- Script finished for all IP addresses. ---")


if __name__ == "__main__":
    main()