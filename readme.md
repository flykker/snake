# Snake

Snake automation CI/CD instrument with fork BuildDSL as a new PyML DSL Python Language:

* Add anonymous function
* Add try, except
* Add import pyml modules
* Generate yaml file from DSL syntax


Snake - in future Alternative Terrafrom, Ansible, Jenkins etc

Snake is simple support yout infrastracture as code

## Installation and run

    $ git clone https://github.com/flykker/snake.git
    $ cd snake
    $ snake -h
    $ snake -f ci.pyml

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
    use "git"
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

## Examples dynamic generate k8s pod manifest with ENV and Terrafrom Synatax (HCL)


```py
# yaml_builder module in root path project
from yaml_builder import yamlBuilder as yaml

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
    labels = {"stand": env['name']}
  }

  spec {
    replica = env['replica']
    containers = [
      {"name":"nginx","image":"nginx"}
    ]
  }
}

def builder = yaml(env=env[stand])
def yaml_pod = builder(pod)
print yaml_pod
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
  replica: 1
  containers:
  - name: nginx
    image: nginx

```

## Examples how generate ansible-playbook with ENV and Terrafrom Synatax (HCL).And also why not create roles with PyML ...


```py
# yaml_builder module in root path project
from ansible import ansible

def env = {
  "dev": {
    "name": "dev",
    "containerPort": 8888,
    "replica": 1,
    "db_name": "base_dev",
    "path_name": "/opt/syngx",
  },
  "prod": {
    "name": "prom",
    "containerPort": 8888,
    "replica": 3,
    "db_name": "base_prod",
    "path_conf": "/opt/syngx"
  }
}

def stand = "prod"

def playbook_db = {
    name = "Example DB"
    hosts = "db"

    vars {
      db_name = self.env["db_name"]
    }

    tasks {
      task {
        name = "Install library DB"

        with_items = [
          "python-pgsql",
          "python-db",
        ]
      }

      task {
        name = "Update DB"
      }
    }
}

def playbook = ansible(env=env[stand])

# def tasks = playbook([playbook_web,playbook_db])
def tasks = playbook([playbook_db])

print tasks
```

```yaml
# prints:
---
- hosts: db
  name: Example DB
  vars:
    db_name: base_prod  
  tasks:
  - name: Install library DB
    with_items:
    - python-pgsql
    - python-db
  - name: Update DB

```

More examples in path examples

