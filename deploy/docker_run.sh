#!/bin/bash
cd /app/qpc
QPC_COMMAND="${1}"
if [ "${QPC_COMMAND}" = "man" ]; then
  shift
  man "${@}"
elif [ -n "${QPC_COMMAND}" ]; then
  poetry run qpc "${@}"
else
  echo "Usage:"
  echo "   $ alias qpc=\"docker run -it -v ~/.config/qpc:/root/.config/qpc \\"
  echo "                               -v ~/.local/share/qpc:/root/.local/share/qpc \\"
  echo "                               quipucords-cli\""
  echo "   $ qpc [--help] <args>"
  echo "   $ qpc man <args>"
  exit 1
fi
