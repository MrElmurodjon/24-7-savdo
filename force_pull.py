import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('83.69.135.18', username='user', password='A6ciWF8m9oR7wcG8WaQ6')
cmds = [
    "echo 'A6ciWF8m9oR7wcG8WaQ6' | sudo -S git config --global --add safe.directory /var/www/savdo247",
    "cd /var/www/savdo247 && echo 'A6ciWF8m9oR7wcG8WaQ6' | sudo -S git pull origin main",
    "echo 'A6ciWF8m9oR7wcG8WaQ6' | sudo -S systemctl restart savdo247"
]
for c in cmds:
    stdin, stdout, stderr = client.exec_command(c)
    print('OUT:', stdout.read().decode('utf-8', errors='ignore'))
    print('ERR:', stderr.read().decode('utf-8', errors='ignore'))
client.close()
