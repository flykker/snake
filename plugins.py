import hvac
import hvac.v1
import requests
import builddsl.closure


def getGlobalValues(parent: builddsl.closure.ObjectTarget) -> dict:
    if hasattr(parent, "_parent"):
        return getGlobalValues(parent._parent)

    return parent._target["values"]


class Vault:
    def __init__(self) -> None:
        self.client = None
        self.closure = None
        self.values:dict = None
        self.data:dict = None
        self.token = ""
        
    def __call__(self, data:dict, closure = None):
        self.closure = closure
        self.values = getGlobalValues(self.closure.parent)
        self.data = data
        self._connect()
        self._login()
        closure(self)

    def _connect(self):
        print(f"Connect to Vault, hostname: {self.data['url']}")
        self.client = hvac.Client(
            url=self.data["url"],
            namespace=self.data["namespace"],
            verify=False
        )
    
    def _login(self):
        print(f"Login in Vault")

        result = self.client.auth.approle.login(
            role_id=self.data["role_id"],
            secret_id=self.values.get("VAULT_SECRETID")
        )

        self.token = result["auth"]["client_token"]
    
    def kv(self, path:str, mount_point:str) -> dict:
        print(f"Print secrets {mount_point} {path}")
        data = self.client.secrets.kv.v1.read_secret(
            path=path,
            mount_point=mount_point
        )["data"]
        return data
    
    def wrap(self, data:dict) -> str:
        print(f"Wrap data")
        headers = {
            "X-Vault-Token": self.token,
            "X-Vault-Wrap-TTL": "1800"
        }

        response = requests.post(
            url=self.data["url"] + "v1/" + self.data["namespace"] + "/sys/wrapping/wrap",
            headers=headers,
            verify=False,
            json=data
        )

        if response.status_code != 200:
            print("error while wrapping secret, http status code: {0}".format(response.status_code))
            return

        return response.json()["wrap_info"]["token"]
    
    def unwrap(self, token:str):
        response = requests.post(
            url=self.data["url"] + "v1/" + self.data["namespace"] + "/sys/wrapping/unwrap",
            headers={"X-Vault-Token": token},
            verify=False
        )

        if response.status_code != 200:
            print("error while unwrapping secret, http status code: {0}".format(response.status_code))
            return

        return response.json()["data"]


import socket
import re

from pssh.clients import SSHClient

SSH_USERNAME = "SSH_USERNAME"
SSH_PASSWORD = "SSH_PASSWORD"

class FieldError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)

class SSH:
    def __init__(self):
        self.closure = None
        self.client = None
        self.values = None
        self.hostname = ""
        self.username = ""
        self.password = ""
        self.pkey = ""
        self.directory = []

    def __call__(self, data:dict, closure=None):
        self.closure = closure
        self.values = getGlobalValues(self.closure.parent)
        self.hostname, self.username, self.password, self.pkey = self._check_data(data)
        self._connect()
        closure(self)
        if self.client is not None:
            print("Disconnect")
            self.client.disconnect()

    def _check_data(self, data:dict):
        pkey = self._check_value(data, "pkey", "SSH_PKEY", requirement=False)
        if "-----BEGIN OPENSSH PRIVATE KEY-----" in pkey:
            pkey = bytes(pkey, "utf-8")
        return (self._check_value(data, "hostname", "SSH_HOSTNAME"),
                self._check_value(data, "username", "SSH_USERNAME"), 
                self._check_value(data, "password", "SSH_PASSWORD", requirement=False),
                pkey)
    
    def _check_value(self, data:dict, name:str, name_in_values: str, requirement: bool =True) -> str:
        if data.get(name, "") == "":
            if self.values.get(name_in_values, "") == "":
                if requirement:
                    raise FieldError(f"Value {name} or {name_in_values} is empty or not found")
                return ""
            else:
                return self.values.get(name_in_values)
        else:
            return data.get(name)


    def _connect(self):
        print(f"Connect to server {self.hostname}")
        
        self.client = SSHClient(self.hostname, user=self.username, password=self.password, pkey=self.pkey)

    def _return_command_with_directory(self, command: str) -> str:
        output = ""
        for dir in self.directory:
            output += dir
        output += command
        return output

    def run(self, command: str) -> str:
        output = self.client.run_command(self._return_command_with_directory(command), use_pty=True)

        return_output = {
            "stdout": "",
            "stderr": "",
            "exit_code": None
        }

        for line in output.stdout:
            return_output["stdout"] = return_output["stdout"]+line+"\n"
            print(line)
        for line in output.stderr:
            return_output["stderr"] = return_output["stderr"]+line
            print(line)
        return_output["exit_code"] = output.exit_code
        return return_output
    
    def dir(self, name: str, closure=None):
        prefix = "cd " + name + " && "
        self.directory.append(prefix)
        closure(self)
        del self.directory[-1]

