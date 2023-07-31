import csv
import difflib

def compare_configs(file1, file2, output_file):
    config1 = read_config_file(file1)
    config2 = read_config_file(file2)

    differences = find_differences(config1, config2)

    write_to_csv(output_file, differences)

def read_config_file(file_path):
    with open(file_path, 'r') as file:
        config = file.readlines()
    return config

def find_differences(config1, config2):
    differences = []
    for line1, line2 in zip(config1, config2):
        if line1 != line2:
            differences.append((line1.strip(), line2.strip()))
    return differences

def write_to_csv(output_file, differences):
    with open(output_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Config 1', 'Config 2'])
        writer.writerows(differences)

# Usage example
compare_configs('OT-ENG-ACC-SW-01_7723.txt', 'BL-LoneTree-SWSTK_7623.txt', 'config_diff.csv')
