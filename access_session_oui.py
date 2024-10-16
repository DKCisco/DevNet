import paramiko
import re
import getpass
import manuf

def ssh_and_run_command(ip, username, password, command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(ip, username=username, password=password)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        ssh.close()
        return output
    except paramiko.AuthenticationException:
        print(f"Authentication failed for IP: {ip}")
        return None
    except paramiko.SSHException as e:
        print(f"SSH connection failed for IP: {ip}, Error: {str(e)}")
        return None
    except Exception as e:
        print(f"An error occurred for IP: {ip}, Error: {str(e)}")
        return None

def find_mac_addresses_and_ports(output):
    mac_port_pattern = re.compile(r'(\d+)\s+([0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4})\s+\S+\s+(\S+)')
    mac_ports = re.findall(mac_port_pattern, output)
    return mac_ports

def lookup_oui(mac_address):
    p = manuf.MacParser()
    manufacturer = p.get_manuf(mac_address)
    return manufacturer

def main():
    command = "show mac address-table | e All"
    username = input("Enter your username: ")
    password = getpass.getpass("Enter your password: ")
    with open("ip_addresses.txt", "r") as file:
        ip_addresses = [line.strip() for line in file]
    for ip in ip_addresses:
        output = ssh_and_run_command(ip, username, password, command)
        if output is not None:
            mac_ports = find_mac_addresses_and_ports(output)
            for vlan, mac, port in mac_ports:
                manufacturer = lookup_oui(mac)
                with open(f"{ip}_output.txt", "a") as file:
                    file.write(f"VLAN: {vlan}, MAC Address: {mac}, Port: {port}, Manufacturer: {manufacturer}\n")

if __name__ == "__main__":
    main()
