class infra:
  def __init__(self, *args, **kwargs):
    pass

  def __call__(self, closure=None, **kwargs):
    closure(self)

  def di_vm(self, name, closure=None):
    closure(self)
    data = {}
    params = closure.frame.f_locals['localvars']
    var_di = closure.frame.f_globals['di']
    import requests
    #endpoint = "https://api.cloud.sberbank.ru/api/v1/servers"
    endpoint = var_di['host'] + '/api/v1/servers'
    
    if params["joindomain"]:
      params["app_params"] = {
        "joindomain":{"title":"DNS домен","value":"delta.sbrf.ru"}
      }
    del params["joindomain"]

    params['disk'] = params['volume_size']
    
    params["hdd"] = {
      "size": params['volume_size'],
      "type": "sds"
    }
    del params['volume_size']

    data["server"] = params
    data["count"] = 1
    
    headers = {"Authorization": var_di['token'], 'Content-Type': 'application/json', 'Accept': 'application/json'}
    #headers = {'Accept': 'application/json', 'FROM': 'SwaggerUI'}
    print(data, endpoint, headers)

    response = requests.post(endpoint, json=data, headers=headers, verify=False)
    print(response.json())

    #print(requests.get(endpoint, headers=headers, verify=False).json())
