# DevNet: Network Automation & Engineering Utilities

A collection of Python scripts and tools designed for network engineering, infrastructure automation, and security analysis. This repository includes solutions for Cisco IOS management, SolarWinds Orion API integration, IP enrichment, subnet calculation, and various network diagnostics.

## 🛠️ Key Categories & Scripts

### Cisco Configuration & Management
Scripts built using `paramiko` and `netmiko` for automating Cisco network devices.
* **`cisco_config.py` & `SW_Config_*.py`**: Automated configuration deployment, interface discovery, and running-config backups.
* **`Cisco_ACL_Syntax_Logic.py` & `show_ip_access_list.py`**: Retrieve and validate Access Control Lists (ACLs) and SNMP configurations.
* **`access_session_oui.py`**: Scrapes MAC address tables and performs OUI manufacturer lookups.
* **`save_config_local_logic.py`**: SSH into devices and securely backup running configurations locally.

### Network Monitoring & Diagnostics
* **`https_status.py`**: Monitors website uptime and sends alerts via the SendGrid API.
* **`nmap_scan.py`**: Wrapper for Nmap to perform automated OS fingerprinting and port scans.
* **`ping_script.py` & `subnet_ping.py`**: Batch ICMP ping sweeps for single IPs and full subnets.
* **`threaded_dos.py` & `threaded_dos_alert.py`**: Multithreaded network load testing and latency/DNS alerting (intended for authorized homelab/stress testing).
* **`Syslog_Server.py`**: A lightweight UDP syslog listener.

### IPAM, DNS & SolarWinds API
* **`IPAM_Query_IP.py` & `SW_Query_IP2Caption.py`**: Query SolarWinds Orion using SWQL (JSON API) for subnet data and node captions.
* **`Hostname_To_IP.py`**: Bulk DNS resolution from text files.
* **`ip_enricher_whois.py` & `ipinfo_public_lookup.py`**: Enrich IP addresses with RDAP, AWS range mappings, and WHOIS geolocation data.
* **`subnet_calc.py`**: A Tkinter-based GUI calculator for IPv4 CIDR subnetting.

### Data Verification & Utilities
* **`compare_configs.py`**: Generates CSV diffs between network configuration files.
* **`compare_csv.py` & `csv_json_verify_IP.py`**: Parse, compare, and validate network data across CSV and JSON formats.
* **`Time_Tracker_v1_2.py`**: A desktop GUI application for tracking project time and exporting daily summaries to Excel.
* **`CCNP_Quiz.py`**: A local Tkinter GUI study tool for practicing network engineering concepts.
* **`md5_verify.py`**: Local file integrity checking.

## 🚀 Dependencies

Many of these scripts require external Python libraries. You can install the most common dependencies via pip:

```bash
pip install paramiko netmiko requests nmap python-nmap openpyxl sendgrid httpx
