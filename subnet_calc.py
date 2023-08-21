import tkinter as tk
from ipaddress import ip_network, IPv4Address

def subnet_calculator(cidr_notation):
    network = ip_network(cidr_notation, strict=False)
    network_address = network.network_address
    broadcast_address = network.broadcast_address
    number_of_hosts = network.num_addresses - 2
    wildcard_bits = IPv4Address(~int(network.netmask) & 0xFFFFFFFF)
    subnet_mask = network.netmask

    # Calculate usable IP addresses (excluding network and broadcast addresses)
    usable_ips = list(network.hosts())
    usable_ip_range = f"{usable_ips[0]} - {usable_ips[-1]}" if usable_ips else "No usable IPs"

    return {
        "network_address": network_address,
        "broadcast_address": broadcast_address,
        "number_of_hosts": number_of_hosts,
        "wildcard_bits": wildcard_bits,
        "subnet_mask": subnet_mask,
        "usable_ip_range": usable_ip_range
    }

def calculate_subnet():
    cidr_notation = cidr_entry.get()
    result = subnet_calculator(cidr_notation)

    network_address_label.config(text=f'Network Address: {result["network_address"]}')
    broadcast_address_label.config(text=f'Broadcast Address: {result["broadcast_address"]}')
    number_of_hosts_label.config(text=f'Number of Hosts: {result["number_of_hosts"]}')
    wildcard_bits_label.config(text=f'Wildcard Bits: {result["wildcard_bits"]}')
    subnet_mask_label.config(text=f'Subnet Mask: {result["subnet_mask"]}')
    usable_ip_range_label.config(text=f'Usable IP Range: {result["usable_ip_range"]}')

root = tk.Tk()
root.title("Subnet Calculator")

cidr_label = tk.Label(root, text="Enter CIDR Notation (e.g., 192.168.1.0/24):")
cidr_label.pack()
cidr_entry = tk.Entry(root)
cidr_entry.pack()

calculate_button = tk.Button(root, text="Calculate", command=calculate_subnet)
calculate_button.pack()

network_address_label = tk.Label(root, text="")
network_address_label.pack()
broadcast_address_label = tk.Label(root, text="")
broadcast_address_label.pack()
number_of_hosts_label = tk.Label(root, text="")
number_of_hosts_label.pack()
wildcard_bits_label = tk.Label(root, text="")
wildcard_bits_label.pack()
subnet_mask_label = tk.Label(root, text="")
subnet_mask_label.pack()
usable_ip_range_label = tk.Label(root, text="")
usable_ip_range_label.pack() # Label to display usable IP range

root.mainloop()
