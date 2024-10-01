import os 
from pssh.clients import SSHClient

class SSH:

    def __init__(self):
        pass
    
    def __call__(self, closure=None):
        pass
        #closure(self)

    def connect(self, manifest):
        
        host = 'tvldd-coo000040.delta.sbrf.ru'
        cmd = 'uname'
        client = SSHClient(host)

        host_out = client.run_command(cmd)
        for line in host_out.stdout:
            print(line)
        exit_code = host_out.exit_code

client = SSH()
client.connect()