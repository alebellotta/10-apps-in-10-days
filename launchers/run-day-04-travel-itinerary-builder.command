#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_FILE="${REPO_ROOT}/day-04-travel-itinerary-builder.log"

echo "Starting Day 04 Travel Itinerary Builder..."
echo "Writing launcher output to ${LOG_FILE}"
echo "" > "${LOG_FILE}"

if "${REPO_ROOT}/scripts/run_streamlit_app.sh" "apps/day-04-travel-itinerary-builder" 2>&1 | tee -a "${LOG_FILE}"; then
  exit 0
fi

echo ""
echo "Launcher failed. Review ${LOG_FILE} for details."
echo "Press Enter to close this window."
read -r _
