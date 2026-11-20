#!/usr/bin/env bash
# Runs on the Mochahost server; credentials stay in a private server file.
set -euo pipefail
app_dir=${1:?Application directory required}
python_bin=${2:?Application Python executable required}
env_file=${3:?Private server environment file required}
commit=${4:?Checked commit required}
[[ "$app_dir" = /* && "$python_bin" = /* && "$env_file" = /* ]]
[[ "$commit" =~ ^[0-9a-f]{40}$ ]]
cd -- "$app_dir"
[[ -f manage.py && -f passenger_wsgi.py && -x "$python_bin" ]]
[[ -z "$(git status --porcelain --untracked-files=no)" ]] || { echo 'Tracked server changes must be resolved before deployment.' >&2; exit 1; }
[[ "$(git branch --show-current)" = master ]]
git fetch origin master
# A queued older run must never deploy a revision that is no longer master.
[[ "$(git rev-parse origin/master)" = "$commit" ]] || { echo 'Master has moved; deploy the newer run instead.' >&2; exit 1; }
git merge --ff-only "$commit"
[[ "$(git rev-parse HEAD)" = "$commit" ]]
set -a
source "$env_file"
set +a
: "${DJANGO_SECRET_KEY:?Missing production secret}" "${PORTFOLIO_DB_PASSWORD:?Missing database password}"
"$python_bin" -m pip install -r requirements.txt
"$python_bin" manage.py check --settings=portfolio_site.production
"$python_bin" manage.py migrate --noinput --settings=portfolio_site.production
# Production uses WHITENOISE_USE_FINDERS; no separate static copy is required.
mkdir -p tmp
touch tmp/restart.txt
printf 'Deployed %s and requested Passenger restart.\n' "$commit"
