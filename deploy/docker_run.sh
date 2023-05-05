#!/bin/bash
cd /app/qpc
QPC_COMMAND="${1}"
shift
if [ "${QPC_COMMAND}" == "qpc" ]; then
  poetry run qpc "$@"
elif [ "${QPC_COMMAND}" == "man" ]; then
  man "${@}"
else
  echo "Unknown command ${QPC_COMMAND} specified."
  echo ""
  echo "Usage:"
  echo "   $ alias dsc=\"docker run -it -v ~/.config/qpc:/root/.config/qpc \\"
  echo "                               -v ~/.local/share/qpc:/root/.local/share/qpc \\"
  echo "                               quipucords-cli\""
  echo "   $ dsc <command> <args>"
  echo ""
  echo "     where <command> is one of:"
  echo "       qpc <args>"
  echo "       man <args>"
  exit 1
fi
