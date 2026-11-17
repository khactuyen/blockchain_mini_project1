"""Execute every notebook cell and retain real Ganache outputs for submission."""
import os
from pathlib import Path
import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
os.environ['JUPYTER_PATH'] = str(ROOT / '.venv' / 'share' / 'jupyter') + os.pathsep + os.environ.get('JUPYTER_PATH', '')
path = ROOT / 'CommunityProposalBoard.ipynb'
notebook = nbformat.read(path, as_version=4)
client = NotebookClient(notebook, timeout=120, kernel_name='community-board', resources={'metadata': {'path': str(ROOT)}}, allow_errors=False)
try:
    client.execute()
finally:
    nbformat.write(notebook, path)
errors = [output for cell in notebook.cells if cell.cell_type == 'code' for output in cell.get('outputs', []) if output.output_type == 'error']
assert not errors, errors
code_cells = [cell for cell in notebook.cells if cell.cell_type == 'code']
assert all(cell.execution_count is not None for cell in code_cells)
output = '\n\n'.join(''.join(item.get('text', '')) for cell in code_cells for item in cell.get('outputs', []) if item.output_type == 'stream')
assert 'RESULT: 11/11 checks passed.' in output
(ROOT / 'docs').mkdir(exist_ok=True)
(ROOT / 'docs' / 'notebook-output.txt').write_text(output, encoding='utf-8')
print(f'Executed {len(code_cells)} code cells; no cell errors.')
print('Real notebook outputs saved in CommunityProposalBoard.ipynb and docs/notebook-output.txt.')
print(output[-1800:])
