import os, sys
from pathlib import Path

file = Path(__file__).resolve()
sys.path.append(str(file.parent))
sys.path.append(os.getcwd())
print('here')