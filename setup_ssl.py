import paramiko
import sys
import time

HOST = "83.69.135.18"
PORT = 22
USER = "user"
PASSWORD = "A6ciWF8m9oR7wcG8WaQ6"

def setup_ssl():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)
        print("Connected. Setting up SSL...")

        ssl_script = """#!/bin/bash
set -e

# Install certbot
apt-get install -y certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d savdo-24-7.uz -d www.savdo-24-7.uz \
    --non-interactive \
    --agree-tos \
    --email admin@savdo-24-7.uz \
    --redirect

# Auto-renew cron
(crontab -l 2>/dev/null; echo "0 12 * * * certbot renew --quiet") | crontab -

echo "SSL setup complete!"
"""

        sftp = client.open_sftp()
        with sftp.file('/tmp/setup_ssl.sh', 'w') as f:
            f.write(ssl_script)
        sftp.close()

        command = f"echo '{PASSWORD}' | sudo -S bash /tmp/setup_ssl.sh"
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                data = stdout.channel.recv(4096)
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
            time.sleep(0.2)
        
        remaining = stdout.read()
        if remaining:
            sys.stdout.buffer.write(remaining)
            sys.stdout.buffer.flush()

        exit_status = stdout.channel.recv_exit_status()
        print(f"\nExit status: {exit_status}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    setup_ssl()
