"""Compile one Rust module before and after the real AMM staging recipe."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve(); tools = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(repo / 'scripts/amm_sell'))
import workspace_recipe
from test_workspace_recipe_staging import SourceContainmentTests

fixture = SourceContainmentTests(); fixture.setUp()
try:
    source = fixture.source; root = fixture.root
    module = source / 'programs/pump-amm/src/target/mod.rs'
    module.parent.mkdir(); module.write_text('pub fn answer() -> u8 { 7 }\n')
    (source / 'programs/pump-amm/src/lib.rs').write_text('mod target;\npub fn answer() -> u8 {target::answer()}\n')
    environment = dict(os.environ, CARGO_HOME=str(root / 'cargo-home'), RUSTC=str(tools / 'rustc'))
    environment.pop('RUSTC_WRAPPER', None); environment.pop('RUSTC_WORKSPACE_WRAPPER', None)
    environment.pop('CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER', None)
    manifest = source / 'programs/pump-amm/Cargo.toml'
    subprocess.run([str(tools / 'cargo'), 'generate-lockfile', '--offline', '--manifest-path', str(manifest)],
                   cwd=root, env=environment, check=True, capture_output=True, timeout=30)
    before = subprocess.run([str(tools / 'cargo'), 'build', '--offline', '--locked', '--release',
                             '--manifest-path', str(manifest), '--target-dir', str(root / 'target-before')],
                            cwd=root, env=environment, capture_output=True, text=True, timeout=45)
    staged = root / 'staged'
    report = workspace_recipe.stage(source, staged)
    after = subprocess.run([str(tools / 'cargo'), 'build', '--offline', '--locked', '--release',
                            '--manifest-path', str(staged / 'Cargo.toml'), '--target-dir', str(root / 'target-after')],
                           cwd=root, env=environment, capture_output=True, text=True, timeout=45)
    print(json.dumps({'source_build_returncode': before.returncode, 'stage_report': report,
                      'staged_module_exists': (staged / module.relative_to(source)).exists(),
                      'staged_build_returncode': after.returncode, 'staged_build_stderr': after.stderr}, indent=2))
finally:
    fixture.doCleanups()
