def convert_to_lowercase(mac_addresses):
    return [mac.lower() for mac in mac_addresses]

# Example usage:
mac_addresses = [
    "00:02:4E:18:FA:11",
    "E4:30:22:2D:B0:AA",
    "8C:AE:4C:FF:92:F0",
    "BC:EE:7B:73:6C:5F"
]

lowercase_mac_addresses = convert_to_lowercase(mac_addresses)
print(lowercase_mac_addresses)
