#!/usr/bin/env -S uv run python

#####################################################################################################
"""
Utility for manage dev environment.

Usage:
    ./src/_environment.py [up [d]]
    ./src/_environment.py down
    ./src/_environment.py info
"""
import json
#####################################################################################################

from collections.abc import Mapping, Sequence
from typing import Any, Final, Literal
from logging import getLogger, INFO, StreamHandler


from logging import Logger
from os import getgid, getlogin, getuid
from pathlib import Path
from subprocess import PIPE, Popen
from sys import argv, stdout
from time import sleep
from dataclasses import asdict

from dotenv import load_dotenv
from pydantic.dataclasses import dataclass

from configs.settings import AppSettings

#####################################################################################################

_LOGGER: Final = getLogger(__name__)
_LOGGER.setLevel(INFO)
_LOGGER.addHandler(StreamHandler())

#####################################################################################################

def _create_envs(logger: Logger | None) -> dict[str, str]:
    load_dotenv()
    environment_path: Final = _get_environment_path()
    user_id: Final = getuid()
    group_id: Final = getgid()
    user_name: Final = getlogin()

    if logger is not None:
        logger.info(f'Running environment from "{environment_path}", user_id: {user_id}, user_name: {user_name}, group_id: {group_id}')

    volumes_path: Final[Path] = environment_path.joinpath('volumes')
    volumes_path_pgadmin: Final = volumes_path.joinpath('pgadmin')
    volumes_path_pgadmin.mkdir(parents=True, exist_ok=True)

    volumes_path_postgres: Final = volumes_path.joinpath('postgres')
    volumes_path_postgres.mkdir(parents=True, exist_ok=True)

    _run_command(['chown', '-R', f'{user_id}:{group_id}', str(volumes_path_pgadmin), str(volumes_path_postgres)], {})

    app_settings = AppSettings()

    return {
        'VOLUMES_PATH_POSTGRES': str(volumes_path_postgres),
        'VOLUMES_PATH_PGADMIN': str(volumes_path_pgadmin),
        'USER_ID': str(user_id),
        'GROUP_ID': str(group_id),
        'USER_NAME': user_name,
        'POSTGRES_PASSWORD': app_settings.postgres_password,
        'POSTGRES_USER': app_settings.postgres_user,
        'POSTGRES_DB': app_settings.postgres_db,
        'POSTGRES_PORT': str(app_settings.postgres_port),
        'DOCKER_BUILDKIT': '1',
    }

#####################################################################################################

def _get_environment_path() -> Path:
    current_path: Final = Path(__file__).parent.resolve()
    return current_path.parent.joinpath('environment')

#####################################################################################################

def _run_command(cmd: list[str], env: dict[str, str]) -> None:
    with Popen(  # noqa: S603
        cmd,
        stdout=stdout.buffer,
        stderr=stdout.buffer,
        env=env,
        cwd=str(_get_environment_path()),
    ) as proc:
        proc.wait()

#####################################################################################################

def _get_compose_file_path() -> Path:
    environment_path: Final = _get_environment_path()
    compose_file_path: Final = environment_path.joinpath('docker-compose.yml')
    if not compose_file_path.is_file():
        raise ValueError(f'Unable to find "{compose_file_path}"')
    return compose_file_path

#####################################################################################################

DOCKER_COMPOSE_CMD: Final = ('docker', 'compose', '-f', str(_get_compose_file_path()),)

#####################################################################################################

@dataclass(frozen=True, kw_only=True)
class DockerContainerPublishers:
    url: str
    target_port: int
    published_port: int
    protocol: Literal['tcp'] | Literal['udp']

#####################################################################################################

@dataclass(frozen=True, kw_only=True)
class DockerContainerInfo:
    container_id: str
    name: str
    command: str
    # project: str
    service: str
    state: (
        Literal['paused'] | Literal['restarting'] | Literal['removing'] | Literal['running']
        | Literal['dead'] | Literal['created'] | Literal['exited']
    )
    health: str
    exit_code: int
    publishers: Sequence[DockerContainerPublishers]
    env: Mapping[str, str]

#####################################################################################################

def is_all_containers_running(containers: Sequence[DockerContainerInfo] | None = None) -> bool:
    if containers is None:
        containers = get_environment_docker_containers()
    if not containers:
        return False
    return all(container.state == 'running' for container in containers)

#####################################################################################################

def up_environment(logger: Logger | None = None, detached: bool = False) -> None:
    if logger is not None:
        logger.info(f'detached: {detached}')

    env: Final = _create_envs(logger)

    _run_command(list(DOCKER_COMPOSE_CMD) + ['rm', '-svf'], env)

    up_params = list(DOCKER_COMPOSE_CMD) + ['up', '--build', '--remove-orphans']

    if detached:
        up_params.append('-d')
    else:
        up_params.append('--abort-on-container-exit')

    _run_command(up_params, env)

    if detached:
        while not is_all_containers_running():
            sleep(1)

#####################################################################################################

def _get_inspect_info_for_docker_container(container_id: str, logger: Logger | None = None) -> Mapping[str, Any]:
    with Popen(  # noqa: S603, S607
        ['docker', 'inspect', container_id],
        stdout=PIPE,
        stderr=stdout.buffer,
        env=_create_envs(logger),
        cwd=str(_get_environment_path()),
    ) as proc:
        proc.wait()
        out, _err = proc.communicate()
        ret: Final = json.loads(out)[0]
        if not isinstance(ret, Mapping):
            raise ValueError('Invalid docker inspect return')
        return ret

#####################################################################################################

def _get_env_info_for_docker_container(container_id: str, logger: Logger | None = None) -> Mapping[str, str]:
    inspect: Final = _get_inspect_info_for_docker_container(container_id, logger)
    docker_env: Final = inspect.get('Config', {}).get('Env', [])
    ret: dict[str, str] = {}
    for env in docker_env:
        spl = str(env).split('=', 2)
        ret[spl[0]] = spl[1]
    return ret

#####################################################################################################

def get_environment_docker_containers(logger: Logger | None = None) -> Sequence[DockerContainerInfo]:
    with Popen(  # noqa: S603
        list(DOCKER_COMPOSE_CMD) + ['ps', '--format', 'json'],
        stdout=PIPE,
        stderr=stdout.buffer,
        env=_create_envs(logger),
        cwd=str(_get_environment_path()),
    ) as proc:
        proc.wait()
        out, _err = proc.communicate()

        out_str: Final = out.strip()
        if not out_str:
            return []

        docker_container_infos: list[DockerContainerInfo] = []
        for out_part in out_str.split(b'\n'):
            docker_container = json.loads(out_part)
            publishers: list[DockerContainerPublishers] = []
            publishers_local = docker_container.get('Publishers', [])
            if publishers_local is not None:
                for pub in publishers_local:
                    publishers.append(DockerContainerPublishers(
                        url=pub['URL'],
                        target_port=pub['TargetPort'],
                        published_port=pub['PublishedPort'],
                        protocol=pub['Protocol'],
                    ))

            container_id = docker_container['ID']

            docker_container_infos.append(DockerContainerInfo(
                container_id=container_id,
                name=docker_container['Name'],
                command=docker_container['Command'],
                # project=docker_container['Project'],
                service=docker_container['Service'],
                state=docker_container['State'],
                health=docker_container['Health'],
                exit_code=docker_container['ExitCode'],
                publishers=tuple(publishers),
                env=_get_env_info_for_docker_container(container_id),
            ))

        return tuple(docker_container_infos)

#####################################################################################################

def down_environment(logger: Logger | None = None) -> None:
    _run_command(list(DOCKER_COMPOSE_CMD) + ['down'], _create_envs(logger))

#####################################################################################################

def _run(logger: Logger, argv_list: Sequence[str]) -> None:
    if argv_list:
        option = argv_list[0].strip()
    else:
        option = ''

    match option:
        case 'up' | '':
            detached = False
            if len(argv_list) > 1:
                detached = argv_list[1].strip() == 'd'
            up_environment(logger, detached)
        case 'down':
            down_environment(logger)
        case 'info':
            containers_info = get_environment_docker_containers(logger)
            for con_info in containers_info:
                logger.warning(json.dumps(asdict(con_info), indent=4))
        case _:
            raise ValueError(f'Invalid option: {option}')

#####################################################################################################

if __name__ == '__main__':
    _run(_LOGGER, tuple(argv[1:]))

#####################################################################################################
