#! /usr/bin/env bash

set -e
set -x

alembic upgrade head

python -m app.pre_restart