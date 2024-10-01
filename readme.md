# Snake

Snake automation CI/CD instrument with fork BuildDSL as a new PyML DSL Python Language:

* Add anonymous function
* Add try, except
* Add import pyml modules
* Generate yaml file from DSL syntax


Snake - in future Alternative Terrafrom, Ansible, Jenkins etc

Snake is simple support yout infrastracture as code

## Installation and run

    git clone https://github.com/flykker/snake.git
    cd snake && pip3.6 install -r requirements.txt
    snake -h
    snake -f ci.pyml

## Run only stage when need
    $ snake init build -f ci.pyml


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

def di = {
    "token": os.getenv('DI_PORTAL_TOKEN'),
    "host": "",
    "project_id": "", 
    "group_id": ""
}

infra {
    vm "vm" {
      service_name    = "snake_infra_test_vm"
      group_id        = di["group_id"]
      project_id      = di["project_id"]
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

More examples in path examples

