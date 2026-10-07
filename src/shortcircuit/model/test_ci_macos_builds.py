# test_ci_macos_builds.py
"""Regression tests for the macOS CI and build contract.

The packaging decisions from the PySide2 -> PySide6 migration live in CI
configuration and a shell script, not in Python, so these tests lock the
observable contract of those artefacts rather than unit-testing logic:

  * the macOS matrix builds both slices of PySide6's universal2 wheel -- arm64
    on the ``macos-15`` runner, x86_64 on ``macos-15-intel`` -- and the two
    uploads are named apart so neither clobbers the other;
  * the per-mapper ``macholib`` install step is gone (PyInstaller carries it
    itself on darwin);
  * the workflow tracks the Pipfile's Python 3.13 and does not force an x64
    interpreter, so the arm64 runner gets arm64 Python;
  * ``build_mac_installer.sh`` takes the target architecture and hands it to
    PyInstaller as ``--target-arch``, and the dead ``shortcircuit.spec`` is
    gone;
  * ``Pipfile.lock`` stays cross-platform, carrying the Windows-only deps that
    a single-platform ``pipenv lock`` would drop and the Windows CI leg needs.

They live beside the model tests, per the repo convention that tests are
collocated with the code they cover rather than in a top-level ``tests/``
directory. They exercise build/CI configuration, which already lives at the
repo root, so they read those artefacts relative to the repo root.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_WORKFLOW = _REPO_ROOT / '.github' / 'workflows' / 'main.yml'
_BUILD_SCRIPT = _REPO_ROOT / 'build_mac_installer.sh'
_WIN_BUILD_SCRIPT = _REPO_ROOT / 'build_win_installer.bat'
_PIPFILE_LOCK = _REPO_ROOT / 'Pipfile.lock'
_REQUIREMENTS = _REPO_ROOT / 'requirements.txt'

# pipenv resolves the lock for the running platform only, so a lock generated on
# macOS silently drops the Windows-only dependencies PyInstaller needs there.
# pipenv installs from the lock with ``--no-deps``, so those entries must be
# present for the Windows CI leg to install and build.
_WIN32_ONLY_PYINSTALLER_DEPS = {
  'pefile': '==2024.8.26',
  'pywin32-ctypes': '==0.2.3',
  'colorama': '==0.4.6',
}


def _workflow_text():
  return _WORKFLOW.read_text(encoding='utf-8')


def test_macos_legs_build_both_architectures():
  """arm64 on ``macos-15`` and x86_64 on ``macos-15-intel``, both wired up."""
  text = _workflow_text()
  assert '- os: macos-15\n' in text
  assert '- os: macos-15-intel\n' in text
  assert 'arch: arm64' in text
  assert 'arch: x86_64' in text
  assert 'build_mac_installer.sh ${{ matrix.arch }}' in text


def test_macos_artifacts_are_named_per_architecture():
  """Two macOS legs upload the same app; distinct names keep both artifacts."""
  text = _workflow_text()
  assert 'name: shortcircuit-${{ matrix.arch }}.app.tar.gz' in text


def test_macholib_install_step_is_gone():
  """PyInstaller declares macholib for darwin itself; no CI step reinstalls it."""
  assert 'macholib' not in _workflow_text()


def test_workflow_tracks_python_3_13_without_forcing_x64():
  """Match the Pipfile's ``python_version = "3.13"`` and let each runner win."""
  text = _workflow_text()
  assert 'python-version: "3.13"' in text
  assert 'architecture: x64' not in text


def test_build_script_takes_the_target_arch():
  """The arch is stated in the build, not left to the runner's implicit arch."""
  text = _BUILD_SCRIPT.read_text(encoding='utf-8')
  assert '--target-arch' in text


@pytest.mark.skipif(
  sys.platform == 'win32' or shutil.which('bash') is None,
  reason='needs a real bash; Windows has only a WSL stub without a distro',
)
def test_build_script_is_valid_bash():
  subprocess.run(['bash', '-n', str(_BUILD_SCRIPT)], check=True)


def test_dead_spec_file_is_untracked_and_unreferenced():
  """``shortcircuit.spec`` is dead packaging source from the Windows era.

  PyInstaller regenerates a throwaway ``shortcircuit.spec`` next to its
  invocation on every build, so the contract is that the repo no longer
  *tracks* it -- not that the name is absent from the filesystem.
  """
  tracked = subprocess.run(
    ['git', 'ls-files', '--error-unmatch', 'shortcircuit.spec'],
    cwd=_REPO_ROOT,
    capture_output=True,
    text=True,
  )
  assert tracked.returncode != 0, 'shortcircuit.spec is still tracked by git'
  for script in (_BUILD_SCRIPT, _WIN_BUILD_SCRIPT):
    assert 'shortcircuit.spec' not in script.read_text(encoding='utf-8')


def test_lock_keeps_win32_only_pyinstaller_deps():
  """The lock stays cross-platform: a macOS ``pipenv lock`` drops these."""
  develop = json.loads(_PIPFILE_LOCK.read_text(encoding='utf-8'))['develop']
  for name, version in _WIN32_ONLY_PYINSTALLER_DEPS.items():
    assert name in develop, f'{name} missing from the develop lock section'
    assert develop[name]['version'] == version, name
    assert develop[name]['markers'] == "sys_platform == 'win32'", name


def test_requirements_export_includes_win32_only_deps():
  """The generated requirements.txt mirrors the lock's win32 entries."""
  text = _REQUIREMENTS.read_text(encoding='utf-8')
  for name in _WIN32_ONLY_PYINSTALLER_DEPS:
    assert re.search(rf'^{re.escape(name)}\S*==', text, re.MULTILINE), name
