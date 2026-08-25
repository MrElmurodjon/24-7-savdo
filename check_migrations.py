import paramiko

host = "83.69.135.18"
port = 22
username = "user"
password = "A6ciWF8m9oR7wcG8WaQ6"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port, username, password)

stdin, stdout, stderr = client.exec_command("ls -la /var/www/savdo247/marketplace/migrations/")
print("OUT:", stdout.read().decode())

client.close()
