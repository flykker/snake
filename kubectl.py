import os 
import tempfile

class kubectl:

    def __init__(self):
        pass
    
    def __call__(self, closure=None):
        closure(self)

    def apply(self, manifest):        
        yaml_file, filename = tempfile.mkstemp()
        
        try:
            print(manifest.encode())
            os.write(yaml_file, manifest.encode())
            
            from kubernetes import client, config, utils

            k8s_config = client.Configuration()
            config.load_kube_config(client_configuration=k8s_config)
            k8s_config.verify_ssl = False
            #k8s_config.debug = True    

            k8s_client = client.ApiClient(configuration=k8s_config)
            # yaml_file = 'kuber.yml'
            print(filename)
            pod = utils.create_from_yaml(k8s_client, filename, verbose=False)
            print(pod)
        finally:
            pass 
            os.close(yaml_file)
            os.remove(filename)


