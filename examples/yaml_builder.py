from pathlib import Path
import typing as t

import yaml as pyyaml
from pprint import pprint

from mergedeep import merge


class yamlBuilder:

  def __init__(self, env=None, *args, **kwargs):
    self.yaml_obj = {}
    self.env = env

  def get_yaml_path(self, closure, yaml_name=None, yaml_path={}, localvars={}):
    obj = {}
    if hasattr(closure, 'parent'):
      path = closure.frame.f_locals['arguments'][0]
      obj = self.get_yaml_path(closure.parent, yaml_path={path: { yaml_name: localvars}})
      # print(yaml_name)
    else:
      path = closure._frame.f_locals['arguments'][0]
      # print(yaml_name)

      if path == 'root':
        return yaml_path
      obj = self.get_yaml_path(closure._parent, yaml_path={path: yaml_path})
    
    return obj
  
  def var(self, *args, **kwargs):
      pass

  def __anon__func__(self, closure, *args, **kwargs):

    if closure.frame.f_locals['arguments'][0] == 'root':
      name = kwargs['func_name']
      self.yaml_obj[name] = {}
      closure.frame.f_locals['localvars'] = {}
          
      closure(self, name, frame=closure.frame)
    
      localvars = closure.frame.f_locals['localvars']
      merge(self.yaml_obj, { name: localvars} )
    else:
      name = kwargs['func_name']

      closure.frame.f_locals['localvars'] = {}
      closure(self, name, frame=closure.frame)

      localvars = closure.frame.f_locals['localvars']
      merge(self.yaml_obj, self.get_yaml_path(closure, name, localvars=localvars))


  def __call__(self, yaml_name=None, closure=None):
    # print(type(yaml_name))
    if type(yaml_name).__name__ == 'ClosureFunction' or type(yaml_name).__name__ == 'function':
      self.yaml_obj = {}
      yaml_name(self, "root")
      # print("root", yaml_name.frame.f_locals['localvars'])
      
      if 'localvars' in yaml_name.frame.f_locals:
        merge(self.yaml_obj, yaml_name.frame.f_locals['localvars'])
      
      # pprint(self.yaml_obj)
      # print("---")
      # print(pyyaml.dump(self.yaml_obj))
      # return pyyaml.dump(self.yaml_obj)
      from ruamel.yaml import YAML

      import sys
      from ruamel.yaml.comments import CommentedMap as ordereddict
      yaml = YAML()
      yaml.preserve_quotes = True
      yaml.width = 4096
      
      from io import StringIO

      output_stream = StringIO()
      yaml.dump(self.yaml_obj, output_stream)
      out = output_stream.getvalue()
      return out
    else:
      # print("--- " + yaml_name)

      if closure.frame.f_locals['arguments'][0] == 'root':
        self.yaml_obj[yaml_name] = {}
        closure.frame.f_locals['localvars'] = {}
        closure(self, yaml_name)
        
        # print(yaml_name, closure.frame.f_locals['localvars'])
        merge(self.yaml_obj, { yaml_name: closure.frame.f_locals['localvars']} )
      else:
        name = closure.frame.f_locals['arguments'][0]
        
        # print(yaml_name)
        # self.yaml_obj.update( self.get_yaml_path(closure, yaml_name) )
        closure.frame.f_locals['localvars'] = {}
        closure(self, yaml_name)

        # print(yaml_name, closure.frame.f_locals['localvars'])
        localvars = closure.frame.f_locals['localvars']
        # print(self.get_yaml_path(closure, yaml_name, localvars=localvars))
        merge(self.yaml_obj, self.get_yaml_path(closure, yaml_name, localvars=localvars))
      