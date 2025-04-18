#!/usr/bin/env bash

###############################################################################

set -Eeuo pipefail

# For debug output uncomment:
# set -Eeuxo pipefail

###############################################################################

CUR_DIR="${PWD}"

###############################################################################

function exit_handler () {
    # For debug output uncomment:
    # env

    cd "${CUR_DIR}"
}

trap exit_handler ERR
trap exit_handler EXIT

###############################################################################

BASE_DIR="$(dirname "${0}")"
BASE_DIR="$(realpath "${BASE_DIR}")"

###############################################################################

SCRIPTS_DIR="$(realpath "${BASE_DIR}/${LEVEL_DIR:?}")"
if [[ ! -f "${SCRIPTS_DIR}/.base.sh" ]]; then
    echo "ERROR: Invalid script dir: '${SCRIPTS_DIR}'"
    exit 1
fi

###############################################################################

ROOT_DIR="$(realpath "${SCRIPTS_DIR}/..")"
cd "${ROOT_DIR}"
if [[ (! -f './pyproject.toml' ) || (! -f './uv.lock' ) ]]; then
    echo "ERROR: Invalid root dir: '${ROOT_DIR}'"
    exit 1
fi

###############################################################################

REPORTS_DIR="$(realpath "${ROOT_DIR}/reports")"
[[ -d "${REPORTS_DIR}" ]] || mkdir -p "${REPORTS_DIR}"

###############################################################################

PYTHON_VERSION="${PYTHON_VERSION:-3.11}"
RUN_PYTHON="${RUN_PYTHON:-/usr/bin/python${PYTHON_VERSION}}"

###############################################################################
