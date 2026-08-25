import paramiko
import sys

HOST = "83.69.135.18"
PORT = 22
USER = "user"
PASSWORD = "A6ciWF8m9oR7wcG8WaQ6"

def setup_nginx():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)
        
        nginx_conf = """server {
    listen 80;
    server_name savdo-24-7.uz www.savdo-24-7.uz 83.69.135.18;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/savdo247;
    }

    location /media/ {
        root /var/www/savdo247;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""
        # Upload config
        sftp = client.open_sftp()
        with sftp.file('/tmp/savdo247', 'w') as f:
            f.write(nginx_conf)
        sftp.close()
        
        commands = [
            f"echo '{PASSWORD}' | sudo -S mv /tmp/savdo247 /etc/nginx/sites-available/savdo247",
            f"echo '{PASSWORD}' | sudo -S ln -sf /etc/nginx/sites-available/savdo247 /etc/nginx/sites-enabled/",
            f"echo '{PASSWORD}' | sudo -S rm -f /etc/nginx/sites-enabled/default",
            f"echo '{PASSWORD}' | sudo -S systemctl restart nginx",
            f"echo '{PASSWORD}' | sudo -S ufw allow 'Nginx Full'",
        ]
        
        for cmd in commands:
            stdin, stdout, stderr = client.exec_command(cmd)
            stdout.channel.recv_exit_status()
            
        print("Nginx configuration successfully applied!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    setup_nginx()
