from pathlib import Path
import argparse, json
import proof
P = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--repo', type=Path)
args = parser.parse_args()
root = args.repo.resolve() if args.repo else next(
    parent for parent in P.parents
    if (parent / 'evidence/original/mayhem/deployed.so').is_file()
)
print(json.dumps(proof.check(P, root), indent=2))
