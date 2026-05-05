from scapy.all import sniff, conf, get_if_list, IFACES
import sys

def debug():
    print("--- Kaavach Scapy Deep Debug ---")
    print(f"Python: {sys.version}")
    
    interfaces = IFACES.data.values()
    print(f"\nFound {len(interfaces)} interfaces:")
    for iface in interfaces:
        print(f" - [{iface.index}] {iface.name} ({iface.description})")

    print(f"\nDefault Interface: {conf.iface.description if conf.iface else 'None'}")
    
    print("\n--- Testing All Interfaces (Timeout 3s each) ---")
    print("PLEASE GENERATE TRAFFIC (Open a website) CONTINUOUSLY NOW.")
    
    found_active = False
    for iface in interfaces:
        try:
            print(f"Testing {iface.description}...", end=" ", flush=True)
            pkts = sniff(iface=iface, count=1, timeout=3)
            if len(pkts) > 0:
                print(f"SUCCESS! Captured: {pkts[0].summary()}")
                found_active = True
                # Set this as the new default for this session to see if it works
                conf.iface = iface
            else:
                print("No traffic.")
        except Exception as e:
            print(f"Error: {e}")

    if not found_active:
        print("\nCRITICAL: No traffic seen on ANY interface.")
        print("1. Ensure you are running as ADMINISTRATOR.")
        print("2. Ensure Npcap is installed with 'WinPcap API-compatible Mode' checked.")
    else:
        print("\nActive interface(s) found! You may need to specify the interface in your main code.")

if __name__ == "__main__":
    debug()
