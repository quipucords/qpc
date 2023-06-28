#!/bin/bash
cd /app/qpc
QPC_VAR_PROGRAM_NAME="${QPC_VAR_PROGRAM_NAME:-qpc}"
QPC_COMMAND="${1}"
if [ "${QPC_COMMAND}" = "man" ]; then
  shift
  man "${@}"
elif [ -n "${QPC_COMMAND}" ]; then
  poetry run ${QPC_VAR_PROGRAM_NAME} "${@}"
else
  echo "Usage:"
  echo "   $ alias ${QPC_VAR_PROGRAM_NAME}=\"docker run -it -v ~/.config/qpc:/root/.config/qpc:z \\"
  echo "                               -v ~/.local/share/qpc:/root/.local/share/qpc:z \\"
  echo "                               --entrypoint='/app/qpc/deploy/docker_run.sh' \\"
  echo "                               ${QPC_VAR_PROGRAM_NAME}\""
  echo "   $ ${QPC_VAR_PROGRAM_NAME} [--help] <args>"
  echo "   $ ${QPC_VAR_PROGRAM_NAME} man <args>"
  exit 1
fi
