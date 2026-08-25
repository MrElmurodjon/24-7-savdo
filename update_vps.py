import paramiko
import sys

HOST = "83.69.135.18"
PORT = 22
USER = "user"
PASSWORD = "A6ciWF8m9oR7wcG8WaQ6"

def update_and_restart():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)
        
        commands = [
            f"cd /var/www/savdo247 && git pull origin main",
            f"echo '{PASSWORD}' | sudo -S systemctl restart savdo247",
        ]
        
        for cmd in commands:
            print(f"Running: {cmd[:60]}...")
            stdin, stdout, stderr = client.exec_command(cmd)
            sys.stdout.buffer.write(stdout.read())
            sys.stdout.buffer.flush()
            
        print("\nDone! Service restarted.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    update_and_restart()
