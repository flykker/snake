# import yaml
from ruamel.yaml import YAML
import pprint
import sys

data = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: game-demo
data:
  # property-like keys; each key maps to a simple value
  player_initial_lives: "3"
  ui_properties_file_name: "user-interface.properties"

  # file-like keys
  game.properties: |
    enemy.types=aliens,monsters
    player.maximum-lives=5
  user-interface.properties: |
    color.good=purple
    color.bad=yellow
    allow.textmode=true
"""

yaml = YAML()
yaml.preserve_quotes = True

pprint.pprint(yaml.load(data))
print("---")
obj = yaml.load(data)
#print(obj)

from io import StringIO

output_stream = StringIO()
yaml.dump(data, output_stream)
out = output_stream.getvalue()
print(out)
