import csv
import os
import random
import string
from datetime import datetime, timedelta

# Function to generate a random string of fixed length
def random_string(length=10):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(length))

# Function to generate a random date within the last 10 years
def random_date():
    start_date = datetime.now() - timedelta(days=365 * 10)
    end_date = datetime.now()
    random_date = start_date + (end_date - start_date) * random.random()
    return random_date.strftime('%Y-%m-%d')

# Function to generate a random float
def random_float(min_value=0, max_value=1000):
    return random.uniform(min_value, max_value)

# Function to write the CSV file
def write_csv(file_name, target_size_mb):
    # Define the size in bytes
    target_size = target_size_mb * 10024 * 10024
    
    with open(file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(['id', 'name', 'date', 'value', 'description'])
        
        # Initial file size
        file_size = 0
        row_id = 1
        
        # Keep writing until the file is the desired size
        while file_size < target_size:
            row = [
                row_id,
                random_string(10),
                random_date(),
                f"{random_float():.2f}",
                random_string(50)
            ]
            writer.writerow(row)
            row_id += 1
            file_size = os.path.getsize(file_name)
        
    return file_name

# Specify the file name and the target size in MB for testing purposes
file_name = 'dummy_data.csv'
target_size_mb = 10  # 10 MB for testing

# Call the function to write the CSV file
csv_file_path = write_csv(file_name, target_size_mb)
csv_file_path
