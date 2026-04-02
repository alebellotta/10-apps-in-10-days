#!/bin/bash

set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <app-directory>"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
APP_DIR="${REPO_ROOT}/$1"

if [ ! -d "${APP_DIR}" ]; then
  echo "App directory not found: ${APP_DIR}"
  exit 1
fi

if [ ! -f "${APP_DIR}/app.py" ]; then
  echo "Missing app.py in ${APP_DIR}"
  exit 1
fi

if [ ! -f "${APP_DIR}/requirements.txt" ]; then
  echo "Missing requirements.txt in ${APP_DIR}"
  exit 1
fi

if ! command -v python3.11 >/dev/null 2>&1; then
  echo "Python 3.11 is required but was not found on this machine."
  echo "Install Python 3.11, then re-run this launcher."
  exit 1
fi

PYTHON_BIN="python3.11"

VENV_DIR="${APP_DIR}/.venv"
PYTHON_VENV="${VENV_DIR}/bin/python"

if [ ! -x "${PYTHON_VENV}" ]; then
  echo "Creating virtual environment in ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

VENV_VERSION="$("${PYTHON_VENV}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [ "${VENV_VERSION}" != "3.11" ]; then
  echo "Existing virtual environment uses Python ${VENV_VERSION}. Recreating with Python 3.11."
  rm -rf "${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

echo "Checking dependencies for $(basename "${APP_DIR}")"
if ! "${PYTHON_VENV}" -c "import streamlit" >/dev/null 2>&1; then
  "${PYTHON_VENV}" -m pip install --upgrade pip
  "${PYTHON_VENV}" -m pip install -r "${APP_DIR}/requirements.txt"
fi

cd "${APP_DIR}"
echo "Launching Streamlit app from ${APP_DIR}"
exec "${VENV_DIR}/bin/streamlit" run app.py
