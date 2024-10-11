# Snake

Snake automation CI/CD instrument with fork BuildDSL as a new PyML DSL Python Language:

* Add anonymous function
* Add try, except
* Add import pyml modules
* Generate yaml file from DSL syntax
* Add Plugins


Snake - in future Alternative Terrafrom, Ansible, Jenkins etc

Snake is simple support yout infrastracture as code

## Installation and run

    git clone https://github.com/flykker/snake.git
    cd snake && pip3.6 install -r requirements.txt
    ./snake -h
    ./snake -f examples/ci.pyml

## Run only stage when need
    ./snake init build -f examples/ci.pyml


## Quickstart

```groovy

def env = {
    "dev": {'name': 'dev', 'containerPort': 8888, 'replica': 1},
    "prod": {'name': 'prod', 'containerPort': 8888, 'replica': 3}
}

def stand = "prod"

pipe {
  stage "Init" {
    # install modules httpx
    pip "httpx"
    
    print env[stand]
  }

  stage "Build" {
    print "CI Build"
  }

  stage "Deploy" {
    print "Deploy"
  }
}

# prints:
Run stage: Init
Install and import httpx
Use: git
{'name': 'prod', 'containerPort': 8888, 'replica': 3}
Run stage: Build
CI Build
Run stage: Deploy
Deploy
```

## Examples Pipeline + dynamic generate k8s pod manifest with ENV and Terrafrom Synatax (HCL)


```py
# yaml_builder module in root path project
from yaml_builder import yamlBuilder as yaml

plugins {
  use "kubectl.kubectl"
}

def env = {
    "dev": {'name': 'dev', 'containerPort': 8888, 'replica': 1},
    "prod": {'name': 'prod', 'containerPort': 8888, 'replica': 3}
}

def stand = "prod"

def pod =  {
  apiVersion = "v1"
  kind = "Pod"
  
  metadata {
    name = "static-web"
    namespace = "default"
    labels = {"stand": env['name']}
  }

  spec {
    containers = env['containers'] or [
      {"name":"nginx","image":"nginx"}
    ]
  }
}

def stand = "prod"
env["manifest"] = {}

pipe {
  stage "Init" {
    pip "kubernetes"

    # sh "git clone https://gitverse.ru/flykker/snake.git git_snake"

    print env[stand]
  }

  stage "Build manifest" {
    print "Build manifest"
    def builder = yaml(env=env[stand])
    env["manifest"] = builder(pod)
  }

  stage "Deploy manifest" {
    
    # Save manifest to file  and With use console kubectl
    #sh("kubectl apply --dry-run=client -f kuber.yaml " )
    
    # Without use console kubectl only Python Kubernetes API
    kubectl {
      apply env["manifest"]
    }
  }
}
```

```yaml
# prints:
apiVersion: v1
kind: Pod
metadata:
  name: static-web
  labels:
    stand: prod
spec:
  containers:
  - name: nginx
    image: nginx

# Kubectl deploy to k8s + return logout
```

## Examples create VM on infrastracture with Terrafrom Synatax (HCL)


```py
import os

plugins {
  use "infra.infra"
}

def env = {
    "token": os.getenv('DI_PORTAL_TOKEN'),
    "host": "",
    "project_id": "", 
    "group_id": ""
}

infra {
    vm "vm" {
      service_name    = "snake_infra_test_vm"
      group_id        = env["group_id"]
      project_id      = env["project_id"]
      virtualization  = "openstack"
      ir_group        = "linux"
      ir_type         = "os_linux"
      os_name         = "linux"
      os_version      = ""
      flavor          = "m1.tiny"
      volume_size     = 30
      region          = ""
      zone            = ""
      fault_tolerance = "stand-alone"
      greenfield      = "false"
      internet_access = "false"
      volumes         = []
      joindomain      = ""
    }

    # postActions {
        
    # }
}
```

## Examples run ssh + vault plugins - alternative Ansible


```py
# Example run 
#
# ./snake -f examples/ansible.pyml -v VAULT_SECRETID=12345 SSH_USERNAME=user SSH_PASSWORD=pass

plugins {
    use "plugins.SSH"
    use "plugins.Vault"
}

def paramSecman = {
    "url": "http://localhost:8200/",
    "namespace": "CREDS",
    "role_id": "5a1136ec-be56-8567-7732-8c82c4c83f31"
}
def checks = {
    "CPU": {"threshold":1,"command":"grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage}'"},
    "MEM":{"threshold":70,"command":"free | grep Mem | awk '{print $3/$2 * 100.0}'"},
    "HDD":{"threshold":40,"command":"df -h / | awk '{print $5}'| sed '2!d' | sed 's/%//'"},
}

pipe {
    vault paramSecman {
        print "Secman"
        data = kv(mount_point: "A/DPMPARSER/APP/SEC/KV", path: "SSH")
        ssh {"hostname": "localhost", "username": data["username"], "pkey": data["pkey"]} {

            for check,value in checks.items():
                stage "Check "+check {
                    def currentValue=run(value["command"])
                    currentValue=currentValue["stdout"].replace("\n","")
                    if float(currentValue)>=float(value["threshold"]):
                        print("Error !!! "+check+"="+currentValue+"% and this value more than threshold="+str(value["threshold"])+"%")
                }
        }
    }
}
```

More examples in path examples

