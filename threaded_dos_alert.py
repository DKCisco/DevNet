import socket
import time
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Configuration for SMTP
smtp_server = 'smtp-gateway.test.com'  # Replace with your SMTP server
smtp_port = 25  # Replace with your SMTP port
smtp_user = 'test@test.com'  # Replace with your email
#smtp_password = 'your-email-password'  # Replace with your email password
email_recipient = 'test@test.com'  # Replace with your recipient email

# Server details
target_ip = '192.168.1.1'  # Replace with the target IP address
port = 22
test_num = 0

# Thresholds for alerts
dns_threshold = 500  # milliseconds
latency_threshold = 1000  # milliseconds
packet_loss_threshold = 10  # percent

def send_alert(message):
    """Send an email alert using SMTP."""
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = email_recipient
    msg['Subject'] = 'Network Performance Alert'
    msg.attach(MIMEText(message, 'html'))
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user)
            server.sendmail(smtp_user, email_recipient, msg.as_string())
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

def run_test():
    global test_num
    total_attempts = 10
    successful_tests = 0
    results = []

    for _ in range(total_attempts):
        dns_start = time.time()
        try:
            ip_address = target_ip  # Directly use the IP address
            dns_end = time.time()
            dns_time = (dns_end - dns_start) * 1000  # Convert to milliseconds

            latency_start = time.time()
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip_address, port))
                latency_end = time.time()
                latency = (latency_end - latency_start) * 1000  # Convert to milliseconds

                successful_tests += 1
                test_num += 1
                results.append(f"Test number {test_num}: Success, DNS Time: {dns_time:.3f}ms, Latency: {latency:.3f}ms")
                if dns_time > dns_threshold or latency > latency_threshold:
                    send_alert(f"Performance Alert: DNS Time {dns_time:.3f}ms or Latency {latency:.3f}ms exceeded threshold")

        except Exception as e:
            dns_end = time.time()  # Ensure DNS time is captured in case of exceptions
            dns_time = (dns_end - dns_start) * 1000  # Convert to milliseconds
            results.append(f"Test number {test_num}: An error occurred: {e}, DNS Time: {dns_time:.3f}ms")
            if dns_time > dns_threshold:
                send_alert(f"Performance Alert: DNS Time {dns_time:.3f}ms exceeded threshold")

    packet_loss = ((total_attempts - successful_tests) / total_attempts) * 100
    results.append(f"Packet Loss: {packet_loss:.2f}%")
    if packet_loss > packet_loss_threshold:
        send_alert(f"Performance Alert: Packet Loss {packet_loss:.2f}% exceeded threshold")
    return results

while True:
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    results = run_test()
    with open("network_test_results.html", "r") as file:
        existing_content = file.read()
    
    with open("network_test_results.html", "w") as file:
        file.write(f"<html><body><h1>Network Test Results - {current_time}</h1><ul>")
        for result in results:
            file.write(f"<li>{result}</li>")
        file.write("</ul>")
        file.write(existing_content)
        file.write("</body></html>")
    
    time.sleep(10)  # Delay between tests