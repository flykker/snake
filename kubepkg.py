import os 
import tempfile
from pathlib import Path
from builddsl import Context
from builddsl.targets import ObjectTarget, mutable_mapping, chain
from yaml_builder import yamlBuilder
import yaml
import json
import base64

from kubernetes import client, config, utils
from kubernetes.client.rest import ApiException
import re
import urllib3
urllib3.disable_warnings()

MAX_HISTORY = 9
ROLLBACK = False

class kubepkg:

    def __init__(self):
        self.k8s_client = {}
        self.ns = ""
    
    def __call__(self, closure=None):
        closure(self)

    def install(self, path, env):
        try:
            manifest = ''
            yaml_file, filename = tempfile.mkstemp()

            for root, dirs, files in os.walk(path):
                _path = root.split(os.sep)
                for file in files:
                    manifest += f"# Template pyml {root}{file}\n"
                    
                    _pyml = include(name="{0}/{1}".format(root,file), env=env)
                    # print(_pyml)

                    for it in _pyml:
                        builder = yamlBuilder(env=env)
                        manifest += "---\n"
                        manifest += builder(it)

            # print(manifest)            
            os.write(yaml_file, manifest.encode())
            
            from kubernetes import client, config, utils

            # self.k8s_config = client.Configuration()
            config.load_kube_config(client_configuration=self.k8s_config)
            self.k8s_config.verify_ssl = False
            #self.k8s_config.debug = True    

            self.k8s_client = client.ApiClient(configuration=self.k8s_config)
            # client_api = client.CoreV1Api()
            # yaml_file = 'kuber.yml'
            # print(filename)
            # print(getattr(client_api, "patch_namespaced_pod"))
            pod = utils.create_from_yaml(self.k8s_client, filename, verbose=False)
            print(pod)
        finally:
            pass 
            os.close(yaml_file)
            os.remove(filename)

    def update(self, rollback_name, path, env):
        try:
            manifest = ''
            yaml_file, filename = tempfile.mkstemp()

            for root, dirs, files in os.walk(path):               
                _path = root.split(os.sep)
                for file in files:
                    if file == 'pkg.pyml':
                        continue

                    manifest += f"# Template pyml {root}{file}\n"
                    
                    _pyml = include(name="{0}/{1}".format(root,file), env=env)
                    # print(_pyml)

                    for it in _pyml:
                        builder = yamlBuilder(env=env)
                        manifest += "---\n"
                        manifest += builder(it)
            
            # print(manifest)            
            # os.write(yaml_file, manifest.encode())
            
            

            UPPER_FOLLOWED_BY_LOWER_RE = re.compile('(.)([A-Z][a-z]+)')
            LOWER_OR_NUM_FOLLOWED_BY_UPPER_RE = re.compile('([a-z0-9])([A-Z])')

            # self.k8s_config = client.Configuration()
            # config.load_kube_config(client_configuration=self.k8s_config)
            # self.k8s_config.verify_ssl = False
            #self.k8s_config.debug = True   

            # self.k8s_client = client.ApiClient(configuration=self.k8s_config)
            client_api = client.CoreV1Api(self.k8s_client)

            # contexts, active_context = config.list_kube_config_contexts()
            
            # namespace = active_context['context']['namespace']
            namespace = self.ns
            
            # print("NS: " + namespace)

            label_selector = 'owner=kubepkg,name=' + rollback_name
            list_secret = client_api.list_namespaced_secret(namespace=namespace, label_selector=label_selector)
            
            list_secret = sorted(
                list_secret.items, 
                key=lambda it: int(it.metadata.labels['version']),
                reverse=True
            )
            
            # print(list_secret)
            
            if len(list_secret) > 0:
                lastRollback = list_secret[0]
            
                lastVersion = int(list_secret[0].metadata.labels['version'])
            
                lastManifest = base64.b64decode(lastRollback.data['rollback']).decode("utf-8")
            
                # print(lastManifest)
                # print("New: ", manifest)
                updateObj, deleteObj = diffResources(manifest, lastManifest)
            else:
                updateObj = yaml.safe_load_all(manifest)
                deleteObj = []
                lastVersion = 0
            # print(deleteObj)

            for it in updateObj:                
                kind = it["kind"]
                kind = UPPER_FOLLOWED_BY_LOWER_RE.sub(r'\1_\2', kind)
                kind = LOWER_OR_NUM_FOLLOWED_BY_UPPER_RE.sub(r'\1_\2', kind).lower()
                
                name = namespace = it["metadata"]["name"]
                if "namespace" in it["metadata"]:
                    namespace = it["metadata"]["namespace"]
                
                try:
                    resp = getattr(client_api, "patch_namespaced_{0}".format(kind))(body=it, name=name, namespace=namespace)
                    print(f"Patch {it['kind']}/{it['metadata']['name']}")
                    # print(resp)
                except ApiException as e:
                    err = json.loads(e.body)
                    if err['code'] == 404:
                        resp = getattr(client_api, "create_namespaced_{0}".format(kind))(body=it, namespace=namespace)
                        # print(resp)
                        print(f"Created {it['kind']}/{it['metadata']['name']}")
            
            for it in deleteObj:
                # print("Del -", it)
                kind = it["kind"]
                kind = UPPER_FOLLOWED_BY_LOWER_RE.sub(r'\1_\2', kind)
                kind = LOWER_OR_NUM_FOLLOWED_BY_UPPER_RE.sub(r'\1_\2', kind).lower()
                
                name = namespace = it["metadata"]["name"]
                if "namespace" in it["metadata"]:
                    namespace = it["metadata"]["namespace"]
                
                try:
                    resp = getattr(client_api, "delete_namespaced_{0}".format(kind))(name=name, namespace=namespace)
                    print(f"Deleted {it['kind']}/{it['metadata']['name']}")
                    # print(resp)
                except ApiException as e:
                    err = json.loads(e.body)
                    if err['code'] == 404:
                        # resp = getattr(client_api, "create_namespaced_{0}".format(kind))(body=it, namespace=namespace)
                        # print(resp)
                        print(f"Not found {it['kind']}/{it['metadata']['name']}")
                    else:
                        print("Error: ", e)
            
            create_rollback_config(self.k8s_client, rollback_name, namespace, manifest, list_secret, lastVersion)

        finally:
            pass 
            os.close(yaml_file)
            os.remove(filename)

    def delete(self, name):
        try:
            namespace = self.ns
            
            # print("NS: " + namespace)
            client_api = client.CoreV1Api(self.k8s_client)
            label_selector = 'owner=kubepkg,name='+name
            list_secret = client_api.list_namespaced_secret(namespace=namespace, label_selector=label_selector)
            
            list_secret = sorted(
                list_secret.items, 
                key=lambda it: int(it.metadata.labels['version']),
                reverse=True
            )
                        
            if len(list_secret) > 0:
                lastRollback = list_secret[0]
            
                lastVersion = int(list_secret[0].metadata.labels['version'])            
                lastManifest = base64.b64decode(lastRollback.data['rollback']).decode("utf-8")            
                deleteObj = yaml.safe_load_all(lastManifest)
            else:
                print('Not found pkg version for deleted')
                exit(0)
            
            UPPER_FOLLOWED_BY_LOWER_RE = re.compile('(.)([A-Z][a-z]+)')
            LOWER_OR_NUM_FOLLOWED_BY_UPPER_RE = re.compile('([a-z0-9])([A-Z])')

            
            for it in deleteObj:
                kind = it["kind"]
                kind = UPPER_FOLLOWED_BY_LOWER_RE.sub(r'\1_\2', kind)
                kind = LOWER_OR_NUM_FOLLOWED_BY_UPPER_RE.sub(r'\1_\2', kind).lower()
                
                name = namespace = it["metadata"]["name"]
                if "namespace" in it["metadata"]:
                    namespace = it["metadata"]["namespace"]
                
                try:
                    resp = getattr(client_api, "delete_namespaced_{0}".format(kind))(name=name, namespace=namespace)
                    print(f"Deleted {it['kind']}/{it['metadata']['name']}")
                    # print(resp)
                except ApiException as e:
                    err = json.loads(e.body)
                    if err['code'] == 404:
                        print(f"Not found install pkg {it['kind']}/{it['metadata']['name']}")
            
            for it in list_secret:
                # print("Del secret: ", it)
                kind = "Secret"
                kind = UPPER_FOLLOWED_BY_LOWER_RE.sub(r'\1_\2', kind)
                kind = LOWER_OR_NUM_FOLLOWED_BY_UPPER_RE.sub(r'\1_\2', kind).lower()
                
                name = namespace = it.metadata.name
                if it.metadata.namespace != '':
                    namespace = it.metadata.namespace
                
                try:
                    resp = getattr(client_api, "delete_namespaced_{0}".format(kind))(name=name, namespace=namespace)
                    print(f"Deleted {kind}/{it.metadata.name}")
                    # print(resp)
                except ApiException as e:
                    err = json.loads(e.body)
                    if err['code'] == 404:
                        # resp = getattr(client_api, "create_namespaced_{0}".format(kind))(body=it, namespace=namespace)
                        # print(resp)
                        print(f"Not found {kind}/{it.metadata.name}")
                    else:
                        print("Error: ", e)

        finally:
            pass 


    def rollback(self, rollback_name, version=None):
        global ROLLBACK
        ROLLBACK = True
        try:
            
            UPPER_FOLLOWED_BY_LOWER_RE = re.compile('(.)([A-Z][a-z]+)')
            LOWER_OR_NUM_FOLLOWED_BY_UPPER_RE = re.compile('([a-z0-9])([A-Z])')

            # print("Version: "+str(version))
            # self.k8s_config = client.Configuration()
            
            client_api = client.CoreV1Api(self.k8s_client)

            namespace = self.ns
            # print("NS: " + namespace)

            label_selector = 'owner=kubepkg,name=' + rollback_name
            list_secret = client_api.list_namespaced_secret(namespace=namespace, label_selector=label_selector)
            
            list_secret = sorted(
                list_secret.items, 
                key=lambda it: int(it.metadata.labels['version']),
                reverse=True
            )
            
            # print(list_secret)
            
            if len(list_secret) < 2:
                print("Error: Found only one pkg version, not version for Rollback")
                exit(1)

            lastRollback = list_secret[0]
            lastVersion = int(list_secret[0].metadata.labels['version'])

            previousVersion = lastVersion - 1

            if version is not None:
                previousRollback = filter(lambda it: int(it.metadata.labels['version']) == version, list_secret)
                try:
                    previousRollback = list(previousRollback)[0]
                except:
                    print("Error: Not found pkg rollback version {0}".format(version))
                    exit(1)
            else:
                version = previousVersion
                previousRollback = list_secret[1]

            # print(lastVersion)
            
            # for it in list_secret:
            #     _version = int(it.metadata.labels['version'])
                
            #     if _version > lastVersion:
            #         lastVersion = _version
            #         lastRollback = it
            
            lastManifest = base64.b64decode(lastRollback.data['rollback']).decode("utf-8")
            previousManifest = base64.b64decode(previousRollback.data['rollback']).decode("utf-8")
            
            manifest = previousManifest

            # print(lastManifest)
            # print("New: ", manifest)
            updateObj, deleteObj = diffResources(manifest, lastManifest)
            
            # print(deleteObj)

            for it in updateObj:                
                kind = it["kind"]
                kind = UPPER_FOLLOWED_BY_LOWER_RE.sub(r'\1_\2', kind)
                kind = LOWER_OR_NUM_FOLLOWED_BY_UPPER_RE.sub(r'\1_\2', kind).lower()
                
                name = namespace = it["metadata"]["name"]
                if "namespace" in it["metadata"]:
                    namespace = it["metadata"]["namespace"]
                
                try:
                    resp = getattr(client_api, "patch_namespaced_{0}".format(kind))(body=it, name=name, namespace=namespace)
                    print(f"Patch {it['kind']}/{it['metadata']['name']}")
                    # print(resp)
                except ApiException as e:
                    err = json.loads(e.body)
                    if err['code'] == 404:
                        resp = getattr(client_api, "create_namespaced_{0}".format(kind))(body=it, namespace=namespace)
                        # print(resp)
                        print(f"Created {it['kind']}/{it['metadata']['name']}")
            
            for it in deleteObj:
                # print("Del -", it)
                kind = it["kind"]
                kind = UPPER_FOLLOWED_BY_LOWER_RE.sub(r'\1_\2', kind)
                kind = LOWER_OR_NUM_FOLLOWED_BY_UPPER_RE.sub(r'\1_\2', kind).lower()
                
                name = namespace = it["metadata"]["name"]
                if "namespace" in it["metadata"]:
                    namespace = it["metadata"]["namespace"]
                
                try:
                    resp = getattr(client_api, "delete_namespaced_{0}".format(kind))(name=name, namespace=namespace)
                    print(f"Deleted {it['kind']}/{it['metadata']['name']}")
                    # print(resp)
                except ApiException as e:
                    err = json.loads(e.body)
                    if err['code'] == 404:
                        # resp = getattr(client_api, "create_namespaced_{0}".format(kind))(body=it, namespace=namespace)
                        # print(resp)
                        print(f"Not found {it['kind']}/{it['metadata']['name']}")
                    else:
                        print("Error: ", e)
            
            create_rollback_config(self.k8s_client, rollback_name, namespace, manifest, list_secret, lastVersion, rollbackVersion=version)

        finally:
            pass 

    def login(self, host_or_local, ns=None, token=None):
        KUBE_CONFIG = {
            "current-context": "user",
            "contexts": [
                {
                    "name": "user",
                    "context": {
                        "cluster": "default",
                        "user": "token",
                        "namespace": ns
                    }
                },
            ],
            "clusters": [{
                "name": "default",
                "cluster": {
                    "server": str(host_or_local),
                    "insecure-skip-tls-verify": True,
                }
            }],
            "users": [
                {
                    "name": "token",
                    "user": {
                        "token": token,
                    }
                },
                {
                    "name": "oidc",
                    "user": {
                        "auth-provider": {
                            "name": "oidc",
                            "config": {
                                "id-token": ""
                            }
                        }
                    }
                }
            ]
        }

        if host_or_local == "local":
            k8s_config = client.Configuration()
            config.load_kube_config(client_configuration=k8s_config)
            k8s_config.verify_ssl = False
            k8s_config.debug = False

            self.k8s_client = client.ApiClient(configuration=k8s_config)            
            contexts, active_context = config.list_kube_config_contexts()
            
            self.ns = active_context['context']['namespace']
        else:
            self.k8s_client = config.new_client_from_config_dict(
                config_dict=KUBE_CONFIG, context=None,
                client_configuration=None,
                persist_config=True,
                temp_file_path=None
            )
            self.ns = ns
        
        

        

def include(name, env):
  file = Path(name)

  targets = mutable_mapping({'include':include, 'env': env})
    
  incl_ctx = Context(targets)
#   print(incl_ctx.transpile(file.read_text()))
  
  incl_ctx.module_exec(file.read_text(), "kubepkg_list")
  
  import kubepkg_list
  
  return kubepkg_list.__all__

def create_rollback_config(k8s_client, name, namespace, manifest, list_secret, lastVersion, rollbackVersion=None):

    UPPER_FOLLOWED_BY_LOWER_RE = re.compile('(.)([A-Z][a-z]+)')
    LOWER_OR_NUM_FOLLOWED_BY_UPPER_RE = re.compile('([a-z0-9])([A-Z])')

    # self.k8s_config = client.Configuration()
    # config.load_kube_config(client_configuration=self.k8s_config)
    # self.k8s_config.verify_ssl = False
    #self.k8s_config.debug = True   

    # self.k8s_client = client.ApiClient(configuration=self.k8s_config)
    client_api = client.CoreV1Api(k8s_client)
    
    label_selector = 'owner=kubepkg,name=' + name
    
    # list_secret = client_api.list_namespaced_secret(namespace=namespace, label_selector=label_selector)
    # print(list_secret)

    rollback_conf = client.V1Secret()

    next_version = lastVersion + 1
    
    rollback_name = f"kubepkg.rollback.{name}.v{next_version}"
    rollback_conf.metadata = client.V1ObjectMeta(
        name=rollback_name, 
        labels = {'version': str(next_version), 'owner': 'kubepkg', 'name': name}
    )
    rollback_conf.type = "Opaque"

    import base64
    rollback_conf_data = base64.b64encode(manifest.encode("utf-8")).decode("utf-8")
    rollback_conf.data = {"rollback": rollback_conf_data}

    # print(rollback_conf)
    
    try:
        # pass
        resp = client_api.create_namespaced_secret(namespace=namespace, body=rollback_conf)
    except ApiException as e:
        print(f"Error: {e.body}")
        # err = json.loads(e.body)
        # if err['code'] == 404:
        #     print(f"Not found install pkg {it['kind']}/{it['metadata']['name']}")
    
    for it in list_secret[MAX_HISTORY:]:
        # print("Del secret: ", it)
        kind = "Secret"
        kind = UPPER_FOLLOWED_BY_LOWER_RE.sub(r'\1_\2', kind)
        kind = LOWER_OR_NUM_FOLLOWED_BY_UPPER_RE.sub(r'\1_\2', kind).lower()
        
        name = namespace = it.metadata.name
        if it.metadata.namespace != '':
            namespace = it.metadata.namespace
        
        try:
            resp = getattr(client_api, "delete_namespaced_{0}".format(kind))(name=name, namespace=namespace)
            # print(f"Deleted {kind}/{it.metadata.name}")
            # print(resp)
        except ApiException as e:
            err = json.loads(e.body)
            if err['code'] == 404:
                # resp = getattr(client_api, "create_namespaced_{0}".format(kind))(body=it, namespace=namespace)
                # print(resp)
                print(f"Not found {kind}/{it.metadata.name}")
            else:
                print("Error: ", e)

    if ROLLBACK:
        print("PKG is ROLLBACK: OK")
        print("PKG ROLLBACK VERSION: " + str(rollbackVersion))
        print("PKG VERSION: "+str(next_version))
    else:
        print("PKG is DEPLOYED: OK")
        print("PKG VERSION: "+str(next_version))

def diffResources(current, last):
    currentObj = []
    _currentObj = yaml.safe_load_all(current)
    lastObj = yaml.safe_load_all(last)

    # print(current)

    _current = {}
    for it in _currentObj:
        obj = f'{it["apiVersion"]}/{it["kind"].lower()}/{it["metadata"]["name"]}'
        _current[obj] = True
        currentObj.append(it)

    deleteObj = []
    for it in lastObj:
        obj = f'{it["apiVersion"]}/{it["kind"].lower()}/{it["metadata"]["name"]}'
        if not _current.get(obj, False):
            deleteObj.append(it)
    # print("Del:", deleteObj)

    return currentObj, deleteObj#!/usr/bin/env python


