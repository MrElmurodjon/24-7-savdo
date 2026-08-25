import paramiko
import sys

HOST = "83.69.135.18"
PORT = 22
USER = "user"
PASSWORD = "A6ciWF8m9oR7wcG8WaQ6"

def run_cmds():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)

        commands = [
            f"echo '{PASSWORD}' | sudo -S git -C /var/www/savdo247 reset --hard HEAD",
            f"echo '{PASSWORD}' | sudo -S git -C /var/www/savdo247 pull origin main",
            f"echo '{PASSWORD}' | sudo -S systemctl restart savdo247",
        ]

        for cmd in commands:
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read()
            err = stderr.read()
            sys.stdout.buffer.write(out)
            sys.stdout.buffer.write(err)
            sys.stdout.buffer.flush()
        
        print("\nDone - restarted!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run_cmds()
