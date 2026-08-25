import paramiko
import time
import sys

HOST = "83.69.135.18"
PORT = 22
USER = "user"
PASSWORD = "A6ciWF8m9oR7wcG8WaQ6"

def run_deploy():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {HOST}...")
    
    try:
        client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)
        print("Connected!")
        
        # We will create a bash script on the server and run it
        deploy_script = """#!/bin/bash
set -e
echo "Updating packages..."
apt-get update -y
export DEBIAN_FRONTEND=noninteractive
apt-get install -y python3-pip python3-venv git unzip nginx sqlite3

echo "Cloning repository..."
if [ -d "/var/www/savdo247" ]; then
    echo "Directory exists, pulling latest..."
    cd /var/www/savdo247
    git pull origin main
else
    echo "Cloning..."
    mkdir -p /var/www
    git clone https://github.com/MrElmurodjon/24-7-savdo.git /var/www/savdo247
    cd /var/www/savdo247
fi

echo "Setting up Virtualenv..."
python3 -m venv /var/www/savdo247/venv
/var/www/savdo247/venv/bin/pip install -r /var/www/savdo247/requirements.txt

echo "Setting up .env file..."
cat << 'EOF' > /var/www/savdo247/.env
SECRET_KEY=django-insecure-prod-key-7d9a8f6s5d4f3g2h1j
DEBUG=False
ALLOWED_HOSTS=*
BOT_TOKEN=8850442172:AAFHqFDQK1WPUleqNhEm7KGGjpquITibq5c
CHANNEL_ID=@qishloq_hayoti_savdo_24
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
EOF

echo "Running migrations..."
/var/www/savdo247/venv/bin/python /var/www/savdo247/manage.py migrate
echo "Collecting static files..."
/var/www/savdo247/venv/bin/python /var/www/savdo247/manage.py collectstatic --noinput

echo "Setting permissions..."
chown -R www-data:www-data /var/www/savdo247
chmod -R 775 /var/www/savdo247

echo "Setting up systemd service..."
cat << 'EOF' > /etc/systemd/system/savdo247.service
[Unit]
Description=24/7 Savdo - Django + Telegram Bot
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/savdo247
Environment="PYTHONIOENCODING=utf-8"
ExecStart=/var/www/savdo247/venv/bin/python run.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable savdo247
systemctl restart savdo247

echo "Deployment completed successfully!"
"""
        
        # Upload the script
        sftp = client.open_sftp()
        with sftp.file('/tmp/deploy.sh', 'w') as f:
            f.write(deploy_script)
        sftp.close()
        
        # Execute the script
        command = f"echo '{PASSWORD}' | sudo -S bash /tmp/deploy.sh"
        print("Executing deployment script on server...")
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        
        # Stream output
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                data = stdout.channel.recv(1024)
                sys.stdout.buffer.write(data)
                sys.stdout.flush()
            if stderr.channel.recv_ready():
                data = stderr.channel.recv(1024)
                sys.stderr.buffer.write(data)
                sys.stderr.flush()
            time.sleep(0.1)
            
        print("\nExit status:", stdout.channel.recv_exit_status())
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run_deploy()
