import paramiko
import sys

HOST = "83.69.135.18"
PORT = 22
USER = "user"
PASSWORD = "A6ciWF8m9oR7wcG8WaQ6"

def check_logs():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)
        command = f"echo '{PASSWORD}' | sudo -S journalctl -u savdo247 -n 50 --no-pager"
        stdin, stdout, stderr = client.exec_command(command)
        
        sys.stdout.buffer.write(b"--- LOGS ---\n")
        sys.stdout.buffer.write(stdout.read())
        sys.stdout.buffer.write(b"\n--- STDERR ---\n")
        sys.stdout.buffer.write(stderr.read())
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    check_logs()
