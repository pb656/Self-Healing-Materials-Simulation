#Regenerate all analyses and figures using the current Python interpreter
from pathlib import Path
import subprocess
import sys

if __name__ == '__main__':
    folder = Path(__file__).resolve().parent
    for name in ('simulation.py', 'robustness.py', 'horizon_analysis.py'):
        subprocess.run([sys.executable, str(folder / name)], cwd=folder, check=True)
    print('Finished. Tables, data and figures are in:', folder / 'results')
