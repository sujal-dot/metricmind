#!/usr/bin/env bash
# ============================================================================
# MetricMind — One-Command Startup Script (`./start.sh`)
# ----------------------------------------------------------------------------
# Orchestrates a full local MetricMind dev environment in a single terminal:
#   1. Prerequisite checks (Docker, Python 3.12+, Node, npm)
#   2. Env file auto-copy (backend/.env, cube/.env, frontend/.env.local)
#   3. PostgreSQL via `docker compose up -d` + health-check wait
#   4. Python venv + `pip install -r requirements.txt` only if venv missing
#   5. `npm install` in cube/ and frontend/ only if node_modules missing
#   6. Optional one-shot data import if warehouse is empty
#   7. Cube.dev :4000 -> FastAPI :8000 -> Next.js :3000, each with health check
#   8. Prints a summary banner with URLs
#   9. On Ctrl+C / SIGHUP / SIGTERM: stops Frontend -> Backend -> Cube ->
#      PostgreSQL in reverse order, then prints "Goodbye."
#
# All verbose install/health-check output is appended to `logs/startup.log` so
# the interactive terminal remains readable.
#
# Tested on: Bash 3.2 (macOS) and Bash 5.x (Linux).
# ============================================================================

# ---- Strict mode -----------------------------------------------------------
set -Eeuo pipefail
IFS=$'\n\t'

# ---- Repo root resolution (works when invoked as `./start.sh` or via path) --
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="${SCRIPT_DIR}"
cd "${REPO_ROOT}"

# ---- Paths / ports / timeouts (keep in sync with the repo) -----------------
BACKEND_DIR="${REPO_ROOT}/backend"
FRONTEND_DIR="${REPO_ROOT}/frontend"
CUBE_DIR="${REPO_ROOT}/cube"
LOG_DIR="${REPO_ROOT}/logs"
STARTUP_LOG="${LOG_DIR}/startup.log"

POSTGRES_PORT=5433
CUBE_PORT=4000
BACKEND_PORT=8000
FRONTEND_PORT=3000

POSTGRES_HEALTH_TIMEOUT=60      # seconds
CUBE_HEALTH_TIMEOUT=120         # seconds (cube needs a bit longer to boot)
BACKEND_HEALTH_TIMEOUT=90       # seconds
FRONTEND_HEALTH_TIMEOUT=120     # seconds (next compilation on first run is slow)
HEALTH_POLL_INTERVAL=3          # seconds

MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=12

# PIDs of spawned long-running children (populated as we launch services)
CUBE_PID=""
BACKEND_PID=""
FRONTEND_PID=""
# Tracking: has each service been started by us (so we know whether to stop it)?
STARTED_POSTGRES=0
STARTED_CUBE=0
STARTED_BACKEND=0
STARTED_FRONTEND=0
START_TS=0
SHUTTING_DOWN=0

# ---- ANSI color helpers (NO_COLOR friendly) --------------------------------
if [[ -t 1 && ( -z "${NO_COLOR:-}" ) ]]; then
  _reset=$'\033[0m'; _dim=$'\033[2m'
  _red=$'\033[0;31m'; _green=$'\033[0;32m'; _yellow=$'\033[0;33m'; _cyan=$'\033[0;36m'
  _bold=$'\033[1m'; _ok="✓"; _warn="!"; _err="✗"
else
  _reset=""; _dim=""; _red=""; _green=""; _yellow=""; _cyan=""; _bold=""
  _ok="[OK]"; _warn="[!]"; _err="[ERR]"
fi

# ---- Logging helpers --------------------------------------------------------
mkdir -p "${LOG_DIR}"
# Initialize the log file with a session header (but don't truncate; append).
_start_session_header() {
  local now now_iso
  now_iso="$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")"
  now="$(date)"
  {
    echo "========================================================================"
    echo " MetricMind startup session — ${now} (${now_iso})"
    echo " PWD=${REPO_ROOT}"
    echo " User=$(id -un)"; echo " Shell=${SHELL:-unknown}"; echo " Bash=${BASH_VERSION}"
    echo "========================================================================"
  } >> "${STARTUP_LOG}" 2>/dev/null || true
}
_start_session_header

# `log` appends a structured line to startup.log (never prints to stdout).
log() {
  local sev="$1"; shift
  local ts
  ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")"
  printf '[%s] [%s] %s\n' "${ts}" "${sev}" "$*" >> "${STARTUP_LOG}" 2>/dev/null || true
}

# Pretty console printers.
print_banner() { printf '\n%s%s%s\n' "${_bold}${_cyan}" "$*" "${_reset}"; }
print_step()    { printf '\n%s ...\r'                               "$*"; }
print_ok()      { printf '%s %s%s %s\n'   "${_green}"  "${_ok}"  "${_reset}" "$*"; }
print_warn()    { 1>&2 printf '%s %s%s %s %s%s\n' "${_yellow}" "${_warn}" "${_reset}" "${_yellow}" "$*" "${_reset}"; }
print_fail()    { 1>&2 printf '%s %s%s %s %s%s\n' "${_red}"    "${_err}" "${_reset}" "${_red}"    "$*" "${_reset}"; }
print_ok_over() { printf '\r%s %s%s %s\n' "${_green}" "${_ok}" "${_reset}" "$*"; }

# `run` — tee the command output to startup.log, keep stdout silent.
# Usage: run <label> <cmd...>
run() {
  local label="$1"; shift
  log "RUN" "${label}: $*"
  if ! "$@" >>"${STARTUP_LOG}" 2>&1; then
    log "ERROR" "${label} exited non-zero: $*"
    return 1
  fi
  return 0
}

# ---- Error trap -------------------------------------------------------------
_on_error() {
  local exit_code=$?
  local lineno=${1:-"?"}
  print_fail "start.sh line ${lineno} exited with status ${exit_code}. See ${STARTUP_LOG}."
  log "ERROR" "Line ${lineno} exit=${exit_code}. Invoking graceful shutdown."
  shutdown || true
  exit "${exit_code}"
}
trap '_on_error ${LINENO}' ERR

# ---- Prerequisite check helpers --------------------------------------------
have()      { command -v "$1" >/dev/null 2>&1; }
require_cmd() {
  local name="$1"; shift
  if have "${name}"; then
    local out
    out="$("${name}" "$@" 2>/dev/null | head -n1 || true)"
    log "OK" "Found ${name}: ${out}"
    return 0
  fi
  print_fail "Missing required command: ${name}. Install it, then re-run start.sh."
  log "ERROR" "Missing required command: ${name}"
  exit 1
}

# docker-compose v2 ships as a `docker` plugin. Prefer `docker compose`, fall
# back to standalone `docker-compose` binary, otherwise fail.
# To avoid shellcheck double-quote-versus-word-splitting ambiguity when the
# selected compose command is two words ("docker compose"), expose a thin
# `compose` function that invokes the correct binary(s) and compose_flag which
# holds either "v2-plugin" or "v1-standalone".
COMPOSE_KIND=""
detect_compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    COMPOSE_KIND="v2-plugin"
  elif have docker-compose; then
    COMPOSE_KIND="v1-standalone"
  else
    COMPOSE_KIND=""
  fi
}
compose() {
  case "${COMPOSE_KIND}" in
    v2-plugin)     docker compose "$@" ;;
    v1-standalone) docker-compose "$@" ;;
    *)             echo "compose: not initialized" 1>&2; return 1 ;;
  esac
}

check_python_version() {
  # Accepts Python from PATH or common macOS install locations; returns the
  # selected binary via stdout, or exits with a clear message.
  local bin="" resolved="" v="" maj="" min=""
  local candidates=(
    "${PYTHON_BIN:-}"
    python3.12 python3.13 python3.14 python3 python
    /opt/homebrew/bin/python3.12
    /opt/homebrew/bin/python3.13
    /opt/homebrew/bin/python3.14
    /opt/homebrew/bin/python3
    /usr/local/bin/python3.12
    /usr/local/bin/python3.13
    /usr/local/bin/python3.14
    /usr/local/bin/python3
    /Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12
    /Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13
    /Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14
  )
  for bin in "${candidates[@]}"; do
    [[ -n "${bin}" ]] || continue
    if [[ "${bin}" == */* ]]; then
      [[ -x "${bin}" ]] || continue
      resolved="${bin}"
    else
      resolved="$(command -v "${bin}" 2>/dev/null || true)"
      [[ -n "${resolved}" ]] || continue
    fi
    v="$("${resolved}" -c 'import sys;print("%d.%d"% (sys.version_info[0],sys.version_info[1]))' 2>/dev/null || true)"
    [[ -z "${v}" ]] && continue
    maj="${v%%.*}"; min="${v#*.}"
    if (( maj >= MIN_PYTHON_MAJOR )) && (( maj == MIN_PYTHON_MAJOR ? min >= MIN_PYTHON_MINOR : 1 )); then
      printf '%s' "${resolved}"
      return 0
    fi
  done
  print_fail "Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ required. Install it first."
  log "ERROR" "Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ not found"
  exit 1
}

# ---- Health-check primitives -----------------------------------------------
# wait_for_http <label> <url> <timeout_seconds>
# Polls URL every ${HEALTH_POLL_INTERVAL} until it returns HTTP 2xx, or times out.
wait_for_http() {
  local label="$1" url="$2" t="$3"
  local elapsed=0 code=0
  log "WAIT" "${label} HTTP ${url} (timeout ${t}s)"
  while (( elapsed < t )); do
    code=0
    code="$(curl -k -sS -o /dev/null -w '%{http_code}' --max-time "${HEALTH_POLL_INTERVAL}" "${url}" 2>/dev/null || true)"
    if [[ "${code}" =~ ^[23][0-9][0-9]$ ]]; then
      log "OK" "${label} reachable (HTTP ${code}) after ~${elapsed}s"
      return 0
    fi
    sleep "${HEALTH_POLL_INTERVAL}"
    elapsed=$(( elapsed + HEALTH_POLL_INTERVAL ))
  done
  log "TIMEOUT" "${label} not reachable after ${t}s (last code=${code})"
  return 1
}

# wait_for_postgres_healthy <timeout_seconds>
wait_for_postgres_healthy() {
  local t="$1" elapsed=0 state=""
  log "WAIT" "PostgreSQL container healthy (timeout ${t}s)"
  while (( elapsed < t )); do
    # `docker compose ps` with format gives us the exact health status.
    state="$(DOCKER_CLI_HINTS=false compose ps --format json 2>>"${STARTUP_LOG}" \
      | ${PYTHON_BIN?} -c 'import sys,json
try:
    data=sys.stdin.read().strip()
    if not data: print(""); raise SystemExit
    rows = [json.loads(l) for l in data.splitlines() if l.strip()]
    for r in rows:
      name = r.get("Service") or r.get("service") or ""
      if not name:
        name = (r.get("Name") or "").partition("/")[2]
      if "postgres" in name.lower():
        print(r.get("Health") or r.get("State") or "")
        raise SystemExit
    print("")
except Exception:
    print("")' 2>>"${STARTUP_LOG}" || true)"

    if [[ "${state}" == *"healthy"* ]] || [[ "${state}" == *"Up (healthy)"* ]]; then
      # Bonus: confirm we can actually connect via pg_isready over tcp port.
      if have pg_isready; then
        if pg_isready -h localhost -p "${POSTGRES_PORT}" -U metricmind >>"${STARTUP_LOG}" 2>&1; then
          log "OK" "PostgreSQL healthy (~${elapsed}s) via docker compose + pg_isready"
          return 0
        fi
      else
        log "OK" "PostgreSQL healthy (~${elapsed}s) via docker compose"
        return 0
      fi
    fi
    sleep "${HEALTH_POLL_INTERVAL}"
    elapsed=$(( elapsed + HEALTH_POLL_INTERVAL ))
  done
  log "TIMEOUT" "PostgreSQL not healthy after ${t}s (last state=${state})"
  return 1
}

# ---- Dependency installation (idempotent, only-if-missing) -----------------
ensure_env_file() {
  local target="$1" example="$2"
  if [[ -f "${target}" ]]; then
    log "OK" "env exists: ${target}"
    return 0
  fi
  if [[ -f "${example}" ]]; then
    cp -p "${example}" "${target}"
    print_warn "Created ${target} from ${example}. Edit it to set LLM API keys."
    log "INFO" "copied ${example} -> ${target}"
    return 0
  fi
  print_fail "Missing ${target} and no template ${example} exists."
  exit 1
}

ensure_backend_venv_and_deps() {
  local venv="${BACKEND_DIR}/venv"
  if [[ -x "${venv}/bin/python" ]]; then
    local venv_ok
    venv_ok="$("${venv}/bin/python" -c 'import sys; print(int(sys.version_info >= (3, 12)))' 2>/dev/null || echo 0)"
    if [[ "${venv_ok}" != "1" ]]; then
      print_warn "backend/venv uses Python $("${venv}/bin/python" -V 2>&1); recreating it with $("${PYTHON_BIN}" -V 2>&1)."
      log "WARN" "Removing incompatible backend/venv"
      rm -rf "${venv}"
    fi
  fi
  if [[ ! -d "${venv}" ]]; then
    print_step "Creating backend virtual environment"
    run "Create venv" "${PYTHON_BIN}" -m venv "${venv}"
    print_ok_over "Backend virtual environment created"
  fi
  # Activate (for the remainder of this script execution).
  # shellcheck disable=SC1091
  source "${venv}/bin/activate"
  # Cheap fingerprint: if our top 2 requirements import without error, skip.
  # This is ~instant compared to `pip install -r` every run.
  if "${venv}/bin/python" -c 'import fastapi, uvicorn, pydantic, sqlalchemy, dotenv, pandas' >>"${STARTUP_LOG}" 2>&1; then
    log "OK" "Backend dependencies already installed"
    return 0
  fi
  print_step "Installing backend dependencies (pip -r requirements.txt)"
  run "pip install backend" pip install --upgrade pip
  run "pip install backend" pip install -r "${BACKEND_DIR}/requirements.txt"
  print_ok_over "Backend dependencies installed"
}

ensure_node_modules() {
  local dir="$1" label="$2"
  if [[ -d "${dir}/node_modules" ]]; then
    log "OK" "${label} node_modules already present"
    return 0
  fi
  print_step "Installing ${label} dependencies (npm install)"
  ( cd "${dir}" && run "npm install ${label}" npm install --no-audit --no-fund )
  print_ok_over "${label} dependencies installed"
}

# ---- Data seeding: one-shot if the warehouse is empty ----------------------
database_has_data() {
  # Use python sqlalchemy via the venv so we don't need psql on the host.
  "${BACKEND_DIR}/venv/bin/python" - "$(grep -E '^DATABASE_URL=' "${BACKEND_DIR}/.env" | head -n1 | cut -d= -f2- | tr -d '"')" \
    2>>"${STARTUP_LOG}" <<'PY' || exit 1
import os, sys
url = sys.argv[1] if len(sys.argv)>1 else os.environ.get("DATABASE_URL","")
if not url:
  print("NO_URL"); sys.exit(0)
from sqlalchemy import create_engine, text
try:
    eng = create_engine(url)
    with eng.connect() as c:
        # probe tables we create in import_csv + build_star_schema
        rows = c.execute(text("""
          SELECT table_name FROM information_schema.tables
          WHERE table_schema = 'public'
            AND table_name IN ('regions','fact_sales','dim_customer','import_logs')
        """)).fetchall()
    tables = {r[0] for r in rows}
    if "fact_sales" in tables or "import_logs" in tables or "regions" in tables:
        if "fact_sales" in tables:
            with eng.connect() as c:
                n = c.execute(text("SELECT COUNT(*) FROM fact_sales")).scalar()
            print("FACT_ROWS=" + str(n))
        else:
            print("HAS_TABLES")
    else:
        print("EMPTY")
except Exception as e:
    print("EMPTY")
PY
}

maybe_seed_database() {
  print_step "Checking database contents"
  local res
  res="$(database_has_data || true)"
  log "INFO" "database probe result: ${res}"
  # Treat any mention of "FACT_ROWS=<nonzero>" / "HAS_TABLES" as "has data".
  if [[ "${res}" == "FACT_ROWS="* ]]; then
    local n="${res#FACT_ROWS=}"
    if (( n > 0 )); then
      print_ok_over "Database already contains ${n} fact rows — skipping import"
      return 0
    fi
  fi
  if [[ "${res}" == "HAS_TABLES" ]]; then
    print_ok_over "Database tables exist — skipping import"
    return 0
  fi

  # Otherwise: empty. Run import -> clean -> star build -> validate.
  print_warn "Database empty; running one-shot import pipeline. This takes a minute or two."
  (
    cd "${BACKEND_DIR}"
    run "import_csv"   python scripts/import_csv.py
    run "clean_data"   python scripts/clean_data.py
    run "validate_clean_data" python scripts/validate_clean_data.py
    run "build_star_schema"   python scripts/build_star_schema.py
    run "validate_star_schema" python scripts/validate_star_schema.py
  )
  print_ok "Database seeded successfully"
}

# ---- Lifecycle: start individual services ----------------------------------
start_postgres() {
  print_banner "Starting PostgreSQL..."
  # `docker compose up -d` is idempotent. If the container is already up, it is
  # a no-op (returns 0 quickly), so STARTED_POSTGRES still gets set to 1
  # because we "manage" it from here on for shutdown purposes.
  run "docker compose up -d" compose up -d
  STARTED_POSTGRES=1
  print_step "Waiting for PostgreSQL (healthy)"
  if wait_for_postgres_healthy "${POSTGRES_HEALTH_TIMEOUT}"; then
    print_ok_over "PostgreSQL Ready"
  else
    print_fail "PostgreSQL not healthy after ${POSTGRES_HEALTH_TIMEOUT}s. Try \`docker compose logs -f\`."
    exit 2
  fi
}

start_cube() {
  print_banner "Starting Cube.dev..."

  ensure_node_modules "${CUBE_DIR}" "Cube.dev"

  # If Cube is already running, don't start another instance.
  if curl -fs "http://localhost:${CUBE_PORT}/readyz" >/dev/null 2>&1; then
    print_ok "Cube.dev already running on port ${CUBE_PORT}"
    STARTED_CUBE=0
    return 0
  fi

  (
    cd "${CUBE_DIR}"
    nohup npm run dev >>"${STARTUP_LOG}" 2>&1 < /dev/null &
    echo $! > "${CUBE_DIR}/.start.pid"
  )

  CUBE_PID="$(cat "${CUBE_DIR}/.start.pid" 2>/dev/null || true)"
  rm -f "${CUBE_DIR}/.start.pid"

  STARTED_CUBE=1

  print_step "Waiting for Cube.dev..."

  if wait_for_http \
      "Cube.dev" \
      "http://localhost:${CUBE_PORT}/readyz" \
      "${CUBE_HEALTH_TIMEOUT}"
  then
      print_ok_over "Cube Running"
  else
      print_fail "Cube.dev failed to start."
      exit 3
  fi
}

start_backend() {
  print_banner "Starting Backend..."
  # ensure venv + deps are ready (idempotent)
  ensure_backend_venv_and_deps
  (
    cd "${BACKEND_DIR}"
    nohup uvicorn app.main:app --host 0.0.0.0 --port "${BACKEND_PORT}" --reload \
      >>"${STARTUP_LOG}" 2>&1 < /dev/null & echo $! > "${BACKEND_DIR}/.start.pid"
  )
  BACKEND_PID="$(cat "${BACKEND_DIR}/.start.pid" 2>/dev/null || true)"
  rm -f "${BACKEND_DIR}/.start.pid"
  STARTED_BACKEND=1
  print_step "Waiting for Backend (http://localhost:${BACKEND_PORT}/docs)"
  if wait_for_http "Backend" "http://localhost:${BACKEND_PORT}/docs" "${BACKEND_HEALTH_TIMEOUT}"; then
    print_ok_over "Backend Ready"
  else
    print_fail "Backend not reachable after ${BACKEND_HEALTH_TIMEOUT}s. Check ${STARTUP_LOG}."
    exit 4
  fi
}

start_frontend() {
  print_banner "Starting Frontend..."
  ensure_node_modules "${FRONTEND_DIR}" "Frontend"
  # Note: Next.js `next dev` writes to both stdout and stderr; capture both.
  (
    cd "${FRONTEND_DIR}"
    nohup npm run dev -- --port "${FRONTEND_PORT}" \
      >>"${STARTUP_LOG}" 2>&1 < /dev/null & echo $! > "${FRONTEND_DIR}/.start.pid"
  )
  FRONTEND_PID="$(cat "${FRONTEND_DIR}/.start.pid" 2>/dev/null || true)"
  rm -f "${FRONTEND_DIR}/.start.pid"
  STARTED_FRONTEND=1
  print_step "Waiting for Frontend (http://localhost:${FRONTEND_PORT})"
  if wait_for_http "Frontend" "http://localhost:${FRONTEND_PORT}" "${FRONTEND_HEALTH_TIMEOUT}"; then
    print_ok_over "Frontend Ready"
  else
    print_fail "Frontend not reachable after ${FRONTEND_HEALTH_TIMEOUT}s. Check ${STARTUP_LOG}."
    exit 5
  fi
}

# ---- Graceful shutdown (reverse start order) -------------------------------
kill_group_of() {
  # $1 = PID; return 0 always. Silence errors (process already gone).
  local pid="$1"
  [[ -z "${pid}" ]] && return 0
  # Kill the process group (child pids like `npm -> node -> next` share pgid).
  local pgid
  if pgid="$(ps -o pgid= -p "${pid}" 2>/dev/null | tr -d ' ' || true)"; then
    if [[ -n "${pgid}" ]]; then
      kill -TERM -- "-${pgid}" >>"${STARTUP_LOG}" 2>&1 || true
    fi
  fi
  # Fallback: TERM then KILL the direct pid.
  kill -TERM "${pid}" >>"${STARTUP_LOG}" 2>&1 || true
  ( sleep 3; kill -KILL "${pid}" >>"${STARTUP_LOG}" 2>&1 || true ) &
  return 0
}

wait_pid_gone() {
  local pid="$1" label="$2"
  [[ -z "${pid}" ]] && return 0
  local i=0 max=20
  while (( i < max )); do
    if ! kill -0 "${pid}" >>"${STARTUP_LOG}" 2>&1; then return 0; fi
    sleep 0.5; i=$((i+1))
  done
  log "WARN" "${label} pid ${pid} still alive after ${max} half-seconds; continuing anyway"
  return 0
}

shutdown() {
  if [[ "${SHUTTING_DOWN:-0}" == "1" ]]; then
    return 0
  fi
  SHUTTING_DOWN=1

  local now now_iso dur
  now="$(date)"
  now_iso="$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")"
  dur="$(( $(date +%s) - START_TS ))"
  printf '\n'
  print_banner "Stopping MetricMind..."

  if [[ "${STARTED_FRONTEND:-0}" == "1" ]]; then
    kill_group_of "${FRONTEND_PID}"
    wait_pid_gone "${FRONTEND_PID}" "Frontend"
    print_ok "Frontend Stopped"
    log "STOP" "Frontend (pid=${FRONTEND_PID})"
  fi

  if [[ "${STARTED_BACKEND:-0}" == "1" ]]; then
    kill_group_of "${BACKEND_PID}"
    wait_pid_gone "${BACKEND_PID}" "Backend"
    print_ok "Backend Stopped"
    log "STOP" "Backend (pid=${BACKEND_PID})"
  fi

  if [[ "${STARTED_CUBE:-0}" == "1" ]]; then
    kill_group_of "${CUBE_PID}"
    wait_pid_gone "${CUBE_PID}" "Cube"
    print_ok "Cube Stopped"
    log "STOP" "Cube (pid=${CUBE_PID})"
  fi

  if [[ "${STARTED_POSTGRES:-0}" == "1" ]]; then
    ( compose down >>"${STARTUP_LOG}" 2>&1 || true )
    print_ok "PostgreSQL Stopped"
    log "STOP" "PostgreSQL via docker compose down"
  fi

  log "END" "Shutdown at ${now} (${now_iso}). Total runtime ${dur}s."
  printf '\n%s%sGoodbye.%s\n' "${_bold}" "${_green}" "${_reset}"
}

# SIGINT (Ctrl+C), SIGTERM, SIGHUP (terminal closed) → graceful shutdown.
on_signal() { shutdown; exit 0; }
trap 'on_signal' INT TERM HUP

# ---- Port-conflict detection ------------------------------------------------
check_port_free_or_ours() {
  local port="$1" label="$2"
  # If we are re-running and a previous process already holds the port, that's
  # fine — we'll just fail to start it later and that's handled. If something
  # ELSE (outside our PIDs) holds it, warn loudly (useful UX).
  local holder=""
  if have lsof; then
    holder="$(lsof -nP -iTCP:"${port}" -sTCP:LISTEN -t 2>/dev/null | head -n1 || true)"
  fi
  if [[ -n "${holder}" ]]; then
    # If the holder is one of OUR known PIDs -> fine, will be reused/restarted.
    if [[ "${holder}" == "${CUBE_PID}" || "${holder}" == "${BACKEND_PID}" || "${holder}" == "${FRONTEND_PID}" ]]; then
      return 0
    fi
    print_warn "Port ${port} (${label}) is already in use by PID ${holder}."
    print_warn "  -> If this is a stale MetricMind process, kill it with: kill ${holder}"
    print_warn "  -> Continuing anyway (the new service will likely fail to bind)."
    log "WARN" "Port ${port} (${label}) held by PID ${holder} (not ours)"
  fi
  return 0
}

# ============================================================================
# MAIN
# ============================================================================
main() {
  START_TS="$(date +%s)"
  log "START" "start.sh invoked as: $0 $*"

  # --------------------------------------------------------------------------
  # 1. Prerequisite command checks
  # --------------------------------------------------------------------------
  print_banner "Checking prerequisites"
  require_cmd docker --version
  detect_compose_cmd
  if [[ -z "${COMPOSE_KIND}" ]]; then
    print_fail "Docker Compose (v2 plugin or v1 binary) required."
    exit 1
  fi
  log "OK" "Compose command: ${COMPOSE_KIND}"
  require_cmd node --version
  require_cmd npm --version
  require_cmd curl --version
  # Pick a supported python binary (python3 >= 3.12, or python >= 3.12).
  PYTHON_BIN="$(check_python_version)"
  export PYTHON_BIN
  # COMPOSE_KIND is used by the compose() function in-script; no need to export it.
  print_ok "Prerequisites OK  (Docker, Compose, Node, npm, Python $("${PYTHON_BIN}" -V 2>&1), curl)"

  # --------------------------------------------------------------------------
  # 2. Port conflict pre-flight (advisory only)
  # --------------------------------------------------------------------------
  check_port_free_or_ours "${POSTGRES_PORT}"  "PostgreSQL"
  check_port_free_or_ours "${CUBE_PORT}"      "Cube.dev"
  check_port_free_or_ours "${BACKEND_PORT}"   "FastAPI Backend"
  check_port_free_or_ours "${FRONTEND_PORT}"  "Next.js Frontend"

  # --------------------------------------------------------------------------
  # 3. Env file copies (idempotent)
  # --------------------------------------------------------------------------
  ensure_env_file "${BACKEND_DIR}/.env"        "${BACKEND_DIR}/.env.example"
  ensure_env_file "${CUBE_DIR}/.env"           "${CUBE_DIR}/.env.example"
  if [[ ! -f "${FRONTEND_DIR}/.env.local" ]]; then
    if [[ -f "${FRONTEND_DIR}/.env.local.example" ]]; then
      ensure_env_file "${FRONTEND_DIR}/.env.local" "${FRONTEND_DIR}/.env.local.example"
    else
      printf 'NEXT_PUBLIC_API_BASE_URL=http://localhost:%s\n' "${BACKEND_PORT}" \
        > "${FRONTEND_DIR}/.env.local"
      print_warn "Created ${FRONTEND_DIR}/.env.local with NEXT_PUBLIC_API_BASE_URL."
      log "INFO" "created minimal frontend/.env.local"
    fi
  fi
  print_ok "Environment files in place"

  # --------------------------------------------------------------------------
  # 4. PostgreSQL
  # --------------------------------------------------------------------------
  start_postgres

  # --------------------------------------------------------------------------
  # 5. Backend venv + deps (needed BEFORE seeding, which uses the venv)
  # --------------------------------------------------------------------------
  ensure_backend_venv_and_deps

  # --------------------------------------------------------------------------
  # 6. Optional data seeding (one-shot if DB empty)
  # --------------------------------------------------------------------------
  maybe_seed_database

  # --------------------------------------------------------------------------
  # 7. Cube.dev (needs Postgres up and deps installed)
  # --------------------------------------------------------------------------
  start_cube

  # --------------------------------------------------------------------------
  # 8. FastAPI backend
  # --------------------------------------------------------------------------
  start_backend

  # --------------------------------------------------------------------------
  # 9. Next.js frontend
  # --------------------------------------------------------------------------
  start_frontend

  # --------------------------------------------------------------------------
  # 10. Startup summary banner
  # --------------------------------------------------------------------------
  local total total_m total_s
  total="$(( $(date +%s) - START_TS ))"
  total_m=$(( total / 60 )); total_s=$(( total % 60 ))

  printf '\n'
  printf '%s======================================== %s\n'  "${_bold}${_green}" "${_reset}"
  printf '%s  MetricMind Started Successfully     %s\n'   "${_bold}${_green}" "${_reset}"
  printf '%s  (elapsed %dm %02ds)                  %s\n' "${_dim}" "${total_m}" "${total_s}" "${_reset}"
  printf '%s======================================== %s\n'  "${_bold}${_green}" "${_reset}"
  printf '  Frontend      : %shttp://localhost:%s%s\n'       "${_cyan}" "${FRONTEND_PORT}"  "${_reset}"
  printf '  Dashboard     : %shttp://localhost:%s/dashboard%s\n' "${_cyan}" "${FRONTEND_PORT}"  "${_reset}"
  printf '  AI Chat       : %shttp://localhost:%s/chat%s\n'   "${_cyan}" "${FRONTEND_PORT}"  "${_reset}"
  printf '  Analytics     : %shttp://localhost:%s/analytics%s\n' "${_cyan}" "${FRONTEND_PORT}"  "${_reset}"
  printf '\n'
  printf '  Backend API   : %shttp://localhost:%s/docs%s\n'    "${_cyan}" "${BACKEND_PORT}"   "${_reset}"
  printf '  ReDoc         : %shttp://localhost:%s/redoc%s\n'   "${_cyan}" "${BACKEND_PORT}"   "${_reset}"
  printf '\n'
  printf '  Cube.dev      : %shttp://localhost:%s%s\n' "${_cyan}" "${CUBE_PORT}" "${_reset}"
  printf '  Cube API      : %shttp://localhost:%s/cubejs-api/v1%s\n' "${_cyan}" "${CUBE_PORT}" "${_reset}"
  printf '%s======================================== %s\n'  "${_bold}${_green}" "${_reset}"
  printf '  Press %sCtrl+C%s any time to stop all services.\n'   "${_yellow}" "${_reset}"
  printf '  Startup log   : %s%s%s\n'                        "${_dim}" "${STARTUP_LOG}" "${_reset}"
  printf '\n'

  log "READY" "All 4 services up. Frontend=${FRONTEND_PORT} Backend=${BACKEND_PORT} Cube=${CUBE_PORT} Postgres=${POSTGRES_PORT}."

  # --------------------------------------------------------------------------
  # 11. Keep running forever until signal kills us.
  # --------------------------------------------------------------------------
  # Cheap liveness heartbeat (so `ps` shows something alive, and the log keeps
  # occasional "still here" lines for long-running sessions).
  local hb=0
  while true; do
    sleep 30
    hb=$(( hb + 1 ))
    log "ALIVE" "heartbeat #${hb}. uptime=$(( $(date +%s) - START_TS ))s"
  done
}

main "$@"
