# -*- coding: utf-8 -*-
from pathlib import Path
import typing as t

import yaml as pyyaml
from pprint import pprint

from mergedeep import merge


class ansible:

  def __init__(self, env=None, *args, **kwargs):
    self.ansible_obj = {}
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

  def vars(self, closure, *args, **kwargs):

    if closure.frame.f_locals['arguments'][0] == 'root':
      name = 'vars'
      self.ansible_obj[name] = {}
      closure.frame.f_locals['localvars'] = {}
          
      closure(self, name, frame=closure.frame)
    
      localvars = closure.frame.f_locals['localvars']
      merge(self.ansible_obj, { name: localvars} )
    else:
      name = 'vars'

      closure.frame.f_locals['localvars'] = {}
      closure(self, name, frame=closure.frame)

      localvars = closure.frame.f_locals['localvars']
      merge(self.ansible_obj, self.get_yaml_path(closure, name, localvars=localvars))

  def tasks(self, closure, *args, **kwargs):
      self.ansible_obj['tasks'] = {}
      closure(self)

  def task(self, closure, *args, **kwargs):

      name = 'task'

      closure.frame.f_locals['localvars'] = {}
      closure(self, name, frame=closure.frame)

      localvars = closure.frame.f_locals['localvars']
      #merge(self.ansible_obj, self.get_yaml_path(closure, name, localvars=localvars))
      if  self.ansible_obj['tasks'] != {}:
        self.ansible_obj['tasks'].append(localvars)
      else:
        self.ansible_obj['tasks'] = []
        self.ansible_obj['tasks'].append(localvars)

  def __anon__func__(self, closure, *args, **kwargs):

    if closure.frame.f_locals['arguments'][0] == 'root':
      name = kwargs['func_name']
      self.ansible_obj[name] = {}
      closure.frame.f_locals['localvars'] = {}
          
      closure(self, name, frame=closure.frame)
    
      localvars = closure.frame.f_locals['localvars']
      merge(self.ansible_obj, { name: localvars} )
    else:
      name = kwargs['func_name']

      closure.frame.f_locals['localvars'] = {}
      closure(self, name, frame=closure.frame)

      localvars = closure.frame.f_locals['localvars']
      merge(self.ansible_obj, self.get_yaml_path(closure, name, localvars=localvars))


  def __call__(self, yaml_name=None, closure=None):
    from ruamel.yaml import YAML, representer

    import sys
    from ruamel.yaml.comments import CommentedMap as ordereddict
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.Representer = representer.SafeRepresenter

    from io import StringIO
    output_stream = StringIO()
    
    playbooks = []
    if type(yaml_name).__name__ == 'list':
      for playbook in yaml_name:
        self.ansible_obj = {}
        playbooks.append(self.__call__(playbook))
      
      #pprint(playbooks)
      yaml.dump(playbooks, output_stream)
      out = "---\n" + output_stream.getvalue()
      return out

    
    if type(yaml_name).__name__ == 'ClosureFunction' or type(yaml_name).__name__ == 'function':
      self.ansible_obj = {}
      yaml_name(self, "root")
      # print("root", yaml_name.frame.f_locals['localvars'])
      
      if 'localvars' in yaml_name.frame.f_locals:
        merge(self.ansible_obj, yaml_name.frame.f_locals['localvars'])
      
      # pprint(self.ansible_obj)
      #print("---")
      # print(pyyaml.dump(self.ansible_obj))
      # return pyyaml.dump(self.ansible_obj)
      return self.ansible_obj
    else:
      # print("--- " + yaml_name)

      if closure.frame.f_locals['arguments'][0] == 'root':
        self.ansible_obj[yaml_name] = {}
        closure.frame.f_locals['localvars'] = {}
        closure(self, yaml_name)
        
        # print(yaml_name, closure.frame.f_locals['localvars'])
        merge(self.ansible_obj, { yaml_name: closure.frame.f_locals['localvars']} )
      else:
        name = closure.frame.f_locals['arguments'][0]
        
        # print(yaml_name)
        # self.ansible_obj.update( self.get_yaml_path(closure, yaml_name) )
        closure.frame.f_locals['localvars'] = {}
        closure(self, yaml_name)

        # print(yaml_name, closure.frame.f_locals['localvars'])
        localvars = closure.frame.f_locals['localvars']
        # print(self.get_yaml_path(closure, yaml_name, localvars=localvars))
        merge(self.ansible_obj, self.get_yaml_path(closure, yaml_name, localvars=localvars))
      