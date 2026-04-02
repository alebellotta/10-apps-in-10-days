#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_FILE="${REPO_ROOT}/day-02-classic-game.log"

echo "Starting Day 02 Classic Game..."
echo "Writing launcher output to ${LOG_FILE}"
echo "" > "${LOG_FILE}"

if "${REPO_ROOT}/scripts/run_streamlit_app.sh" "apps/day-02-classic-game" 2>&1 | tee -a "${LOG_FILE}"; then
  exit 0
fi

echo ""
echo "Launcher failed. Review ${LOG_FILE} for details."
echo "Press Enter to close this window."
read -r _
