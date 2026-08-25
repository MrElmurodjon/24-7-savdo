import paramiko

HOST = "83.69.135.18"
PORT = 22
USER = "user"
PASSWORD = "A6ciWF8m9oR7wcG8WaQ6"

def restart_service():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)
        print("Connected. Restarting savdo247 service...")
        
        command = f"echo '{PASSWORD}' | sudo -S systemctl restart savdo247"
        stdin, stdout, stderr = client.exec_command(command)
        
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            print("Service restarted successfully!")
        else:
            print("Error restarting service:", stderr.read().decode('utf-8'))
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    restart_service()
