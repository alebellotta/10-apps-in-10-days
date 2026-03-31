#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/day-03-serie-a-livescore.log"

echo "Starting Day 03 Serie A LiveScore..."
echo "Writing launcher output to ${LOG_FILE}"
echo "" > "${LOG_FILE}"

if "${SCRIPT_DIR}/scripts/run_streamlit_app.sh" "apps/day-03-serie-a-livescore" 2>&1 | tee -a "${LOG_FILE}"; then
  exit 0
fi

echo ""
echo "Launcher failed. Review ${LOG_FILE} for details."
echo "Press Enter to close this window."
read -r _
