# Snake

Snake automation CI/CD instrument with fork BuildDSL as a new PyML DSL Language:

* Add anonymous function
* Add try, except
* Add import pyml modules
* Generate yaml file from DSL syntax


Snake - in future Alternative Terrafrom, Ansible, Jenkins ....
Snake is simple support yout infrastracture

## Installation and run

    $ git clone https://github.com/flykker/snake.git
    $ cd snake && snake -f ci.pyml

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

## Examples generate k8s pod manifest with ENV and Terrafrom Synatx(HCL)


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

More examples in path examples

