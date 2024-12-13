#!/bin/sh
#
# Start jupyter-server for pytest
#
# Required environment variables:
# JUPYTER_SERVER_PORT: Jupyter server localhost port
# JUPYTER_SERVER_TOKEN: Jupyter server token
# JUPYTER_SERVER_ROOT_DIR: Jupyter server root directory
#
if [ -z "${JUPYTER_SERVER_PORT}" ]
then export JUPYTER_SERVER_PORT="9854"
fi
if [ -z "${JUPYTER_SERVER_ROOT_DIR}" ]
then export JUPYTER_SERVER_ROOT_DIR=$(mktemp -dp "/tmp" "jp-server-XXXXXX")
fi
if [ -z "${JUPYTER_SERVER_TOKEN}" ]
then export JUPYTER_SERVER_TOKEN=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 16 && echo)
fi

ROOT_DIR="$(dirname "$0")/.."

echo "Starting jupyter-server in ${JUPYTER_SERVER_ROOT_DIR} at http://localhost:${JUPYTER_SERVER_PORT}"
jupyter-server \
    --port ${JUPYTER_SERVER_PORT} \
    --IdentityProvider.token ${JUPYTER_SERVER_TOKEN} \
    --ServerApp.open_browser False \
    "${JUPYTER_SERVER_ROOT_DIR}" >"${ROOT_DIR}/jupyter_server.log" 2>&1 &
    # --debug \
    # --SQLiteYStore.db_path "${JUPYTER_SERVER_ROOT_DIR}/crdt.db" \
    # --BaseFileIdManager.root_dir "${JUPYTER_SERVER_ROOT_DIR}" \
    # --BaseFileIdManager.db_path "${JUPYTER_SERVER_ROOT_DIR}/crdt.db" \
    # --BaseFileIdManager.db_journal_mode OFF \

wget --retry-connrefused --tries=100 --wait=1 --quiet "http://localhost:${JUPYTER_SERVER_PORT}/api"

echo "Starting pytest in ${ROOT_DIR}..."
pytest $@

pkill jupyter-server
# cat "${ROOT_DIR}/jupyter_server.log"
