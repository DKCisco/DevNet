import csv
import time
import webbrowser
import pyautogui

# Function to read addresses from a CSV file and open them in Google Maps
def open_addresses_in_google_maps(csv_file, x, y):
    with open(csv_file, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            address = row[0]
            url = f"https://www.google.com/maps/search/{address}"
            webbrowser.open(url)
            time.sleep(5)  # Wait for the page to load

            try:
                # Click the "Save" button using the provided x, y coordinates
                pyautogui.click(x, y)
                time.sleep(2)  # Wait for the save action to complete

                # Press the Enter key
                pyautogui.press('enter')
                time.sleep(2)  # Wait for the enter action to complete
            except Exception as e:
                print(f"Could not save address: {address}. Error: {e}")

# Specify the path to your CSV file
csv_file_path = 'addresses.csv'

# Specify the x, y coordinates for the "Save" button click
x_coordinate = 236  # Replace with your x coordinate
y_coordinate = 532   # Replace with your y coordinate

# Call the function to open addresses in Google Maps, click the "Save" button, and press Enter
open_addresses_in_google_maps(csv_file_path, x_coordinate, y_coordinate)