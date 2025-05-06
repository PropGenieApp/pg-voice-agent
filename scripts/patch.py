#!/usr/bin/env -S uv  run -q python

#####################################################################################################

import os
import re
import sys
import sysconfig
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from importlib.metadata import PackageNotFoundError, distribution, packages_distributions
from logging import INFO, Logger, StreamHandler, getLogger
from pathlib import Path
from subprocess import CalledProcessError, run  # noqa: S404
from types import MappingProxyType
from typing import Final, Iterable

#####################################################################################################

_LOGGER: Final = getLogger(__name__)

_STREAM_HANDLER: Final = StreamHandler()
_LOGGER.addHandler(_STREAM_HANDLER)
_LOGGER.setLevel(INFO)

#####################################################################################################

class _OsSystem(Enum):
    WINDOWS = 0
    UNIX = 1
    MACOS = 2
    MIXED = 3

#####################################################################################################

_WINDOWS_LINE_ENDING: Final = b'\r\n'
_UNIX_LINE_ENDING: Final = b'\n'
_MACOS_LINE_ENDING: Final = b'\r'

#####################################################################################################

LINE_ENDINGS: Final = MappingProxyType({
    _OsSystem.WINDOWS: _WINDOWS_LINE_ENDING,
    _OsSystem.UNIX: _UNIX_LINE_ENDING,
    _OsSystem.MACOS: _MACOS_LINE_ENDING,
})

#####################################################################################################

_PIPFILE: Final = 'Pipfile'
_PYPROJECT: Final = 'pyproject.toml'

#####################################################################################################

def _get_project_root_folder_path(logger: Logger) -> Path:
    current_folder = Path(__file__)
    system_root_folder: Final = Path(current_folder.root)

    while current_folder != system_root_folder:
        project_desc_files: list[Path] = []
        for desc_file in (_PYPROJECT, _PIPFILE):
            project_desc_files.extend(current_folder.glob(desc_file))
        if project_desc_files:
            logger.info(f'"{current_folder}" is used as project root folder')
            return current_folder
        current_folder = current_folder.parent

    logger.error('Cannot find any project description files')
    sys.exit(1)

#####################################################################################################

def _get_env_path(logger: Logger, root_folder_path: Path, base_commands: list[str]) -> Path:
    env_path = os.environ.get('VIRTUAL_ENV')
    if env_path is not None:
        env_path = env_path.strip()
    else:
        command: Iterable[str] = []
        if root_folder_path.joinpath(_PIPFILE).exists():
            command = base_commands + ['--venv']
        elif root_folder_path.joinpath(_PYPROJECT).exists():
            command = base_commands + ['env', 'info', '--path']
        else:
            logger.error('Cannot find any project description files')
            sys.exit(1)
        try:
            env_path_output: Final = run(command, capture_output=True, text=True, check=True, cwd=root_folder_path)  # noqa: S603, DUO116
        except CalledProcessError as exc:
            logger.error(exc.stderr, exc_info=exc)
            sys.exit(1)
        env_path = env_path_output.stdout.strip()
    logger.info(f'"{env_path}" is used as env folder')
    return Path(env_path)

#####################################################################################################

def _check_python_runner(python_runner: str, _package_manager: str, root_folder_path: Path) -> bool:
    try:
        run([python_runner, '--version'], capture_output=True, text=True, check=True, cwd=root_folder_path)  # noqa: S603, DUO116
        return True
    except BaseException:  # noqa: B036, PIE786, WPS424  # pylint: disable=broad-exception-caught
        return False

#####################################################################################################

def _get_python_runner(package_manager: str, root_folder_path: Path) -> str | None:
    python_runner = 'python3'
    if _check_python_runner(python_runner, package_manager, root_folder_path):
        return python_runner
    python_runner = 'python3.11'
    if _check_python_runner(python_runner, package_manager, root_folder_path):
        return python_runner
    python_runner = 'python3.10'
    if _check_python_runner(python_runner, package_manager, root_folder_path):
        return python_runner
    return None

#####################################################################################################

def _get_package_name(module_name: str, logger: Logger) -> str | None:
    package_distributions: Final = packages_distributions()
    package_names: Final = package_distributions.get(module_name)

    if package_names is None:
        logger.warning(f'Cannot find package name for module "{module_name}"')
        return None
    elif len(package_names) > 1:
        logger.warning(f'Cannot definitely determine package name for module "{module_name}". Got packages: {package_names}')
        return None

    return package_names[0]

#####################################################################################################

def _get_frozen_requirements(logger: Logger) -> Iterable[str]:
    command: Final = [
        'uv',
        'run',
        'pip',
        'freeze',
    ]
    try:
        raw_frozen_requirements: Final = run(command, check=True, capture_output=True, text=True)  # noqa: S603
    except CalledProcessError as exc:
        logger.error(f'Cannot get frozen requirements. Got exception: {exc}')
        return []

    return raw_frozen_requirements.stdout.split('\n')

#####################################################################################################

def _get_package_commit_id(package_name: str, requirements: list[str], logger: Logger) -> str | None:
    pkg_freeze_info: Final = next((desc for desc in requirements if desc.startswith(f'{package_name} @')), None)
    if pkg_freeze_info is None:
        logger.info(f'Cannot get info from "pip freeze" for package "{package_name}"')
        return None

    commit_id: Final = pkg_freeze_info.split('@')[-1]
    return commit_id.strip()

#####################################################################################################

def _main(logger: Logger) -> int:  # noqa: WPS213
    logger.info('Patching...\n')

    root_folder_path: Final = _get_project_root_folder_path(logger)

    package_manager: str = ''
    if root_folder_path.joinpath(_PIPFILE).exists():
        package_manager = 'pipenv'
    elif root_folder_path.joinpath(_PYPROJECT).exists():
        package_manager = 'uv'
    else:
        logger.error('Cannot find any project description files')
        return 1

    python_runner: Final = _get_python_runner(package_manager, root_folder_path)
    if python_runner is None:
        logger.error('Cannot find python runner')
        return 1

    base_commands: Final = [python_runner, '-m', package_manager]
    logger.info(f'Use base command {base_commands}')

    patches_folder_path: Final = root_folder_path.joinpath('patches')
    python_version: Final = sysconfig.get_python_version()

    if not patches_folder_path.exists():
        logger.warning('Folder with patches was not found')
        return 1

    env_path: Final = _get_env_path(logger, root_folder_path, base_commands)
    site_packages_path: Final = env_path.joinpath('lib', f'python{python_version}', 'site-packages')

    os.chdir(site_packages_path)
    detected_os_by_lineending: Final[dict[Path, _OsSystem]] = {}

    patch_infos: Final = _get_patch_infos(patches_folder_path)
    frozen_requirements: Final = _get_frozen_requirements(logger)

    for module, versioned_patches in patch_infos.items():
        logger.info(f'\nProcessing patch for module "{module}"...')

        package_name = _get_package_name(module, logger)
        if package_name is None:
            logger.warning(f'SKIPPED patch for "{module}": Package not found.')
            continue

        try:
            dist = distribution(package_name)
        except PackageNotFoundError:
            logger.warning(f'SKIPPED patch for "{module}": Module not found.')
            continue
        package_version = dist.version

        patch = _get_latest_patch(package_version, versioned_patches)
        package_commit_id = _get_package_commit_id(package_name, frozen_requirements, logger)

        if patch.commit_id != package_commit_id:
            logger.warning(f'SKIPPED patch for "{module}": Commit ids do not match.')
            logger.warning(f'Commit from patch: {patch.commit_id}')
            logger.warning(f'Commit in package: {package_commit_id}')
            continue

        patch_file = patch.patch_file
        patch_project = site_packages_path.joinpath(module)
        logger.info(f'Patching {patch_file} -> {patch_project} ...')

        try:
            patch_os = _detect_os_by_lineending(patch_file)
        except ValueError as exc2:
            logger.error(exc2, exc_info=exc2)
            return 1

        patched_sign = patch_project.joinpath('___PATCHED___.txt')
        if patched_sign.exists():
            logger.warning(f'SKIPPED {patch_file} => {patch_project}: Module {module} already patched.')
            continue

        patched_filenames = _collect_patched_filenames(patch_file)
        for source_file in patched_filenames:
            patched_filename = site_packages_path.joinpath(source_file)
            detected_os = _detect_os_by_lineending(patched_filename)
            detected_os_by_lineending[patched_filename] = detected_os
            _replace_lineending(patched_filename, detected_os, patch_os)

        try:
            run(['patch', '-p0', '-i', str(patch_file)], check=True, cwd=site_packages_path)  # noqa: S603, S607
        except CalledProcessError as exc3:
            logger.error(f'Cannot patch module {module}: {exc3.stderr}', exc_info=exc3)
            return 1

        patch_sh = patches_folder_path.joinpath(f'{module}.sh')
        if patch_sh.exists():
            logger.info(f'Execute {patch_sh}')
            try:
                run(['bash', patch_sh], check=True, cwd=patch_project)  # noqa: S603, S607
            except CalledProcessError as exc4:
                logger.error(f'Cannot execute {patch_sh}: {exc4.stderr}', exc_info=exc4)
                return 1

        for target_file in patched_filenames:
            patched_filename = site_packages_path.joinpath(target_file)
            _replace_lineending(patched_filename, patch_os, detected_os_by_lineending[patched_filename])

        logger.info(f'Patched {patch_file} -> {patch_project}\n')
    return 0

#####################################################################################################

def _replace_lineending(filename: Path, orig_system: _OsSystem, target_system: _OsSystem) -> None:
    if orig_system == _OsSystem.MIXED or target_system == _OsSystem.MIXED:
        return

    if not filename.exists():
        return

    if orig_system == target_system:
        return

    with open(filename, 'rb') as source_file:
        file_content: Final = source_file.readlines()

    replaced_content: Final[list[bytes]] = []
    for line in file_content:
        replaced_content.append(line.replace(LINE_ENDINGS[orig_system], LINE_ENDINGS[target_system]))

    with open(filename, 'wb') as target_file:
        target_file.writelines(replaced_content)

#####################################################################################################

def _collect_patched_filenames(patch_file: Path) -> list[str]:
    with open(patch_file, encoding='utf-8') as patch:
        file_content: Final = patch.read()
    return re.findall(r'\+{3}\s(.*)\t', file_content)

#####################################################################################################

def _detect_os_by_lineending(filename: Path) -> _OsSystem:
    possible_systems: Final[set[_OsSystem]] = set()

    if not filename.exists():
        return _OsSystem.UNIX

    with open(filename, 'rb') as source_file:
        for line in source_file:
            if line.endswith(_WINDOWS_LINE_ENDING):
                possible_systems.add(_OsSystem.WINDOWS)
            elif line.endswith(_UNIX_LINE_ENDING):
                possible_systems.add(_OsSystem.UNIX)
            else:
                possible_systems.add(_OsSystem.MACOS)

    if len(possible_systems) != 1:
        return _OsSystem.MIXED

    return possible_systems.pop()

#####################################################################################################

def _split_text_by_separator(text: str, separator: str = '@') -> tuple[str, str | None]:
    try:
        first, second = text.split(separator, 1)
    except ValueError:
        first, second = text, None
    return first, second

#####################################################################################################

@dataclass(kw_only=True, frozen=True)
class _VersionedPatch:
    version: str | None
    commit_id: str | None
    patch_file: Path

#####################################################################################################

def _get_patch_infos(patches_folder_path: Path) -> dict[str, list[_VersionedPatch]]:
    patch_infos: Final[dict[str, list[_VersionedPatch]]] = defaultdict(list)

    for patch_file in patches_folder_path.glob('*.patch'):
        package_name, package_info = _split_text_by_separator(patch_file.stem)

        package_version = None
        package_commit_id = None

        if package_info is not None:
            package_version, package_commit_id = _split_text_by_separator(package_info)

        patch_info = _VersionedPatch(version=package_version, commit_id=package_commit_id, patch_file=patch_file)
        patch_infos[package_name].append(patch_info)

    return patch_infos

#####################################################################################################

def _get_latest_patch(package_version: str, versioned_patches: Iterable[_VersionedPatch]) -> _VersionedPatch:
    patch = next((ver_patch for ver_patch in versioned_patches if package_version == ver_patch.version), None)

    if patch is None:
        patch = max(
            versioned_patches,
            key=lambda patch: patch.version if patch.version is not None else '',
        )
    return patch

#####################################################################################################

if __name__ == '__main__':
    sys.exit(_main(_LOGGER))

#####################################################################################################
