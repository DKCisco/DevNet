import ipaddress

network = ipaddress.ip_network('172.31.201.0/24')
for ip in network:
    print(ip)
