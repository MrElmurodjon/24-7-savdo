import paramiko

host = "83.69.135.18"
port = 22
username = "user"
password = "A6ciWF8m9oR7wcG8WaQ6"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port, username, password)

commands = [
    "cd /var/www/savdo247 && sudo /var/www/savdo247/venv/bin/python manage.py migrate",
    "sudo systemctl restart savdo247",
    "sudo systemctl restart savdo247-bot"
]

for cmd in commands:
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    stdin.write(password + "\n")
    stdin.flush()
    print("OUT:", stdout.read().decode())
    print("ERR:", stderr.read().decode())

client.close()
