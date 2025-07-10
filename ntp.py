import time
import ntptime

def sync_clock_to_ntp(num_retries=5):
    time_synced = False

    for i in range(num_retries):
        try:
            print(f"syncing time with NTP server (Attempt {i+1}/{num_retries})...")
            ntptime.settime()
            time_synced = True
            synced_time = time.localtime()
            print(f"time synced successfully. Current UTC time: {synced_time[0]}-{synced_time[1]:02d}-{synced_time[2]:02d} {synced_time[3]:02d}:{synced_time[4]:02d}:{synced_time[5]:02d}")
            break # Exit the loop on success
        except Exception as e:
            print(f"warning: NTP sync attempt failed. {e}")
            time.sleep(2) 

    return time_synced
