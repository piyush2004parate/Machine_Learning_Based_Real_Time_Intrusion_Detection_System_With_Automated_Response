import os
from pathlib import Path
from api import actions

p = actions.LOGS_DIR
print('LOGS_DIR:', p)
print('Exists:', p.exists())
print('List:', list(p.iterdir()) if p.exists() else 'N/A')
