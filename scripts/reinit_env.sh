#!/usr/bin/env bash

LEVEL_DIR='.'
# shellcheck source=.base.sh
source "$(dirname "${0}")/${LEVEL_DIR}/.base.sh"

###############################################################################

bash "${SCRIPTS_DIR}/clean.sh"

###############################################################################

export LANG=en_US.UTF-8
export LANGUAGE=en_US:en
export LC_ALL=en_US.UTF-8

###############################################################################

${RUN_PYTHON} -m pip -V

${RUN_PYTHON} -m pip install --user --break-system-packages --upgrade pip

# maybe install it via pip?
curl -LsSf https://astral.sh/uv/install.sh | sh
uv --version
uv self update
uv cache clean
uv sync

###############################################################################

echo ''
echo 'All have been done successfully.'
echo ''

###############################################################################
