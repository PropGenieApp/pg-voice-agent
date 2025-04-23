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

# maybe install it via pip?
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv --version
uv self update
uv cache clean
uv sync

###############################################################################

echo ''
echo 'All have been done successfully.'
echo ''

###############################################################################
