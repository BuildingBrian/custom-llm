"""Execute custom_llm.ipynb top to bottom without a browser (nbclient).

Only the three student settings in section 1 can be overridden; nothing else in
the notebook is touched. Default: execute in place so outputs are saved into
custom_llm.ipynb. Use --out to write the executed copy elsewhere (smoke tests).
"""
import argparse, re, sys, time
from pathlib import Path
import nbformat
from nbclient import NotebookClient

REPO = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument("--steps", type=int)
p.add_argument("--lr", type=float)
p.add_argument("--corpus")
p.add_argument("--out", default=str(REPO / "custom_llm.ipynb"))
a = p.parse_args()

nb = nbformat.read(REPO / "custom_llm.ipynb", as_version=4)
cell = next(c for c in nb.cells if c.cell_type == "code" and "TRAINING_STEPS" in c.source)
if a.steps is not None:
    cell.source = re.sub(r"^TRAINING_STEPS = \S+", f"TRAINING_STEPS = {a.steps}", cell.source, flags=re.M)
if a.lr is not None:
    cell.source = re.sub(r"^LEARNING_RATE = \S+", f"LEARNING_RATE = {a.lr}", cell.source, flags=re.M)
if a.corpus is not None:
    cell.source = re.sub(r'^CORPUS = "[^"]*"', f'CORPUS = "{a.corpus}"', cell.source, flags=re.M)
print("settings cell now:\n" + cell.source, flush=True)

t0 = time.time()
client = NotebookClient(nb, timeout=None, kernel_name="custom-llm",
                        resources={"metadata": {"path": str(REPO)}})
try:
    client.execute()
finally:
    nbformat.write(nb, a.out)
    print(f"wrote {a.out} after {time.time()-t0:.1f}s", flush=True)
