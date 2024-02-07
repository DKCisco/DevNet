import requests

def get_location(ip_address, token):
    response = requests.get(f'https://ipinfo.io/{ip_address}?token={token}')
    if response.status_code == 200:
        return response.json()
    else:
        return None

ip_addresses = ['8.8.8.8',
                '8.8.8.8',
                '8.8.8.8',]  # replace with your list of IP addresses

token = '66eb0b339ea987'  # replace with your token from IPinfo

for ip in ip_addresses:
    location = get_location(ip, token)
    if location is not None:
        print(f'Location for {ip} is {location["city"]}, {location["region"]}, {location["country"]}')
    else:
        print(f'Could not get location for {ip}')
