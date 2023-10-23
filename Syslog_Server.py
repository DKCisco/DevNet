import socket

def start_syslog_server(address, port, log_file):
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((address, port))
    print(f"Starting syslog server on {address}:{port}")

    with open(log_file, 'a') as f:
        try:
            while True:
                data, addr = server.recvfrom(1024)
                log_entry = f"Received from {addr}: {data.decode('utf-8')}\n"
                print(log_entry, end='')  # Print to console
                f.write(log_entry)  # Write to file
                f.flush()  # Flush the file buffer to ensure real-time writing
        except KeyboardInterrupt:
            print("\nStopping syslog server")
        finally:
            server.close()

if __name__ == "__main__":
    start_syslog_server("0.0.0.0", 5154, "syslog.txt")
import socket

def start_syslog_server(address, port, log_file):
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((address, port))
    print(f"Starting syslog server on {address}:{port}")

    with open(log_file, 'a') as f:
        try:
            while True:
                data, addr = server.recvfrom(1024)
                log_entry = f"Received from {addr}: {data.decode('utf-8')}\n"
                print(log_entry, end='')  # Print to console
                f.write(log_entry)  # Write to file
                f.flush()  # Flush the file buffer to ensure real-time writing
        except KeyboardInterrupt:
            print("\nStopping syslog server")
        finally:
            server.close()

if __name__ == "__main__":
    start_syslog_server("0.0.0.0", 5154, "syslog.txt")