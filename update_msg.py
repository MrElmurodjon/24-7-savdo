import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('83.69.135.18', username='user', password='A6ciWF8m9oR7wcG8WaQ6')
cmd = '''cd /var/www/savdo247 && source venv/bin/activate && python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); django.setup(); from marketplace.models import BotSettings; s = BotSettings.objects.first(); s.welcome_message = s.welcome_message.replace('Quva Nihol', '24/7 Savdo') if s else ''; s.save() if s else None"'''
client.exec_command(cmd)
client.close()
