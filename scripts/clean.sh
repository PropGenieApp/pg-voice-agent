#!/usr/bin/env bash

###############################################################################

LEVEL_DIR='.'
# shellcheck source=.base.sh
source "$(dirname "${0}")/${LEVEL_DIR}/.base.sh"

###############################################################################

cd "${ROOT_DIR}" || exit

###############################################################################

find . -maxdepth 1 -type d -name '*.build' -exec rm -r -f {} +
find . -maxdepth 1 -type d -name 'build' -exec rm -r -f {} +

find . -maxdepth 1 -type d -name '*.dist' -exec rm -r -f {} +
find . -maxdepth 1 -type d -name 'dist' -exec rm -r -f {} +

find . -maxdepth 1 -type f -name '*.spec' -delete

###############################################################################

find . -maxdepth 1 -type d -name 'reports' -exec rm -r -f {} +

find . -maxdepth 1 -type d -name '.*_cache' -exec rm -r -f {} +

###############################################################################

find . -type f -name '*.py[co]' -delete -o -type d -name '__pycache__' -delete

###############################################################################
