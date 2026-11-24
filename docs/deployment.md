# GitHub Actions to Mochahost

The workflow checks pull requests and pushes to `master`. Deployment is disabled
until the repository variable `CPANEL_DEPLOY_ENABLED` is `true`. Once enabled,
a passing push to `master` runs the existing Git pull process over SSH, installs
requirements, checks Django, applies migrations and requests a Passenger restart.
It then checks the public software and support pages.

## One-time setup

1. Confirm Mochahost permits SSH access from GitHub-hosted runners. cPanel's web
   Terminal alone does not guarantee external SSH access. Ask the host for the
   SSH hostname and port if needed.
2. Use a dedicated deployment SSH key. Add its public key to the hosting account
   through cPanel's SSH Access controls. Keep the private key out of this repo.
3. In GitHub repository Settings > Secrets and variables > Actions, add these
   secrets (they may instead be scoped to a `production` environment):

   | Secret | Value |
   | --- | --- |
   | `CPANEL_SSH_HOST` | Mochahost SSH hostname |
   | `CPANEL_SSH_PORT` | SSH port, usually 22 |
   | `CPANEL_SSH_USER` | Hosting account username |
   | `CPANEL_SSH_PRIVATE_KEY` | Dedicated private key, including header/footer |
   | `CPANEL_SSH_KNOWN_HOSTS` | Host key line verified against the hosting provider's fingerprint; include `[host]:port` for a nonstandard port |
   | `CPANEL_APP_DIR` | Absolute path of the existing production Git checkout |
   | `CPANEL_PYTHON_BIN` | Absolute Python executable from cPanel's application virtual environment |
   | `CPANEL_ENV_FILE` | Absolute path to a private shell environment file outside the public web root and Git checkout |

4. Create that private environment file on the server, readable only by your
   hosting user (`chmod 600`). Include the production variables documented in
   README.md, including `DJANGO_SECRET_KEY` and `PORTFOLIO_DB_PASSWORD`. Include
   existing mail and other application settings as needed. This is a trusted
   shell file: quote values properly. cPanel web-app environment settings may
   not be inherited by noninteractive SSH sessions.
5. Ensure the server checkout can still fetch GitHub without a password prompt.
   Confirm it is on `master` with no tracked local modifications. Back up the
   production database before enabling automatic migrations.
6. Add repository **variable** `CPANEL_DEPLOY_ENABLED=true`. Run **Check and deploy
   portfolio** from GitHub's Actions tab with branch `master` for the first run.
   Future pushes deploy automatically after checks pass.

Deployments are serialized, enforce SSH host verification, only fast-forward,
and refuse stale commits or tracked server edits. They do not reset the server
or delete uploaded files. This is an in-place deployment, with no automatic code
or database rollback. If a deployment fails after updating code, inspect Actions
and the hosting error log; resolve the cause and rerun. Database rollback must
be planned separately. Confirm that `tmp/restart.txt` restarts your Passenger
application; otherwise use cPanel's Restart button.

## Interview question documents

The interview-question library adds the `backoffice_interviewquestion` table.
Back up the production database before deploying. Pushing the change to `master`
uses the workflow above to install requirements, run Django checks, apply
migrations, and request a Passenger restart.

For a manual rollout, push the commit to GitHub and, in cPanel Terminal, run
these commands from the production checkout with the production Python
environment active and the required environment variables available:

```sh
git pull --ff-only origin master
python manage.py check --settings=portfolio_site.production
python manage.py migrate --noinput --settings=portfolio_site.production
mkdir -p tmp
touch tmp/restart.txt
```

If `tmp/restart.txt` does not restart the app on this host, restart it through
cPanel's Python application controls. Afterward, open Admin → Interview
questions and verify that the list is accessible. Uploaded attachments are
stored in the database, so no public media-directory configuration is needed.

## Deploy this content update manually

In your usual cPanel Terminal, change to the existing production checkout and run:

```sh
git pull --ff-only origin master
mkdir -p tmp
touch tmp/restart.txt
```

This skills update needs no migration or new dependencies. You can also restart
the app using cPanel's Python application controls. Check `/software/` for Java
and `/support/` for Java/J2EE troubleshooting, stack traces and Splunk afterward.
