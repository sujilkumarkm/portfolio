# portfolio
Django website wehere people can see details about myself. Also going to add an agentic AI Chat bot where people can ask questions about myself.

## Local admin panel

Start MariaDB in XAMPP. Run these commands from the project directory in
PowerShell with the project Python environment active. Set
`PORTFOLIO_DB_PASSWORD` in the environment if your local database account uses a password.

```powershell
python -m pip install -r requirements.txt
$env:PORTFOLIO_DB_USER = 'root'
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Open [the local admin panel](http://127.0.0.1:8000/admin/).
The default MariaDB database is `suji1991_sujil_portfolio`. Use
`PORTFOLIO_DB_NAME`, `PORTFOLIO_DB_HOST`, and `PORTFOLIO_DB_PORT` to override the
connection details. Without `PORTFOLIO_DB_USER`, Django uses the checkout's
SQLite database.

## Mochahost production

Production defaults to the cPanel MySQL user `suji1991_portfolio`, which
already has grants on `suji1991_sujil_portfolio`. Set the Python application's startup file to
`passenger_wsgi.py` and its entry point to `application`. The existing
production configuration uses `https://sujil.net` as the canonical URL.

Set these variables in the Python application environment and make the same
values available in the terminal used for management commands:

| Variable | Value |
| --- | --- |
| `DJANGO_SECRET_KEY` | A private, stable Django secret key |
| `PORTFOLIO_DB_NAME` | `suji1991_sujil_portfolio` |
| `PORTFOLIO_DB_USER` | `suji1991_portfolio` (production default) |
| `PORTFOLIO_DB_PASSWORD` | The MySQL user's password |
| `PORTFOLIO_DB_HOST` | `localhost` (production default, uses the local Unix socket on Linux) |
| `PORTFOLIO_DB_PORT` | `3306` (used for TCP connections) |

From the deployed checkout, with the application's Python environment active:

```sh
python -m pip install -r requirements.txt
python manage.py check --settings=portfolio_site.production
python manage.py migrate --settings=portfolio_site.production
python manage.py createsuperuser --settings=portfolio_site.production
```

The migrations create the tables in the empty database. Run
`createsuperuser` for the initial admin account. Restart the Python application
in cPanel and verify the homepage and `/admin/` over HTTPS.

### Visitor analytics

The public site's analytics prompt appears until a browser saves a preference.
After opt-in, Django uses a signed cookie to count that browser once while the
cookie remains valid (up to one year). Declining or disabling analytics removes
the cookie. Previously counted visits remain in the dashboard. The database
stores a pseudonymous identifier, the first visit time, and available
country/region values. Counts represent browser cookies, so clearing cookies or
using another browser can result in a new count. The analytics feature does
not store raw IP addresses.

For country and region reporting, configure a trusted edge to supply
`CF-IPCountry` and, if available, `CF-Region`. Set
`PORTFOLIO_TRUST_GEO_HEADERS=1` only when the edge overwrites those headers and
direct requests to the origin are blocked. Visits without country data appear
as Unknown. For local header simulation, enable the flag on a loopback-only
server and supply the headers on the consent POST.

### Import a job posting

In **Add application**, paste a direct public HTTPS link into **Posting URL**
and choose **Import from URL**. Review the populated fields and save when
ready. The importer fills blank fields only. Interview scheduling, CVs, and
cover letters are entered separately.

The built-in importer reads structured JobPosting data and supported embedded
posting data, including MongoDB's careers pages. To also extract
details from the page text, set `JOB_IMPORT_OPENAI_API_KEY` in the server
environment and restart Django. The AI step sends public posting text to
OpenAI. It receives no saved application fields or uploaded documents.
`JOB_IMPORT_OPENAI_MODEL` defaults to `gpt-4.1-mini`. Pages that block automated
requests, require sign-in, or load the entire posting through JavaScript may
still need manual entry.

### Interview email

Set `ADMIN_NOTIFICATION_EMAIL` and run
`python manage.py send_interview_emails` to process due mail. Local development
prints messages to the console by default. The sender queues an update on each
stage change and one reminder at 09:00 Europe/Dublin on the day before a
scheduled interview. An upcoming interview added after that time is eligible
for immediate processing. Company details come from the application form.
Add role-specific preparation questions there to use them in place of the
built-in examples.

For production, set `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`,
`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`,
`EMAIL_USE_TLS`, and `DEFAULT_FROM_EMAIL` in the deployment environment.
Schedule `python manage.py send_interview_emails` every five minutes using the
same production settings and database connection as the website. Apply
migrations and create a production administrator separately.


### Members and subscribed notifications

A superuser can add members under **Users** in the admin. Set a valid email,
activate **Staff status**, set a password, and grant the appropriate application
and visitor view permissions (and add/change permissions if needed). Save the
user, then open their record and select **Email notification preferences**:
**New jobs**, **Application updates**, and/or **Interviews**. Only active staff
members receive subscribed emails. User management is restricted to superusers.
Preferences apply across the application's job list. New jobs and edits saved
through admin enter the queue; direct database changes do not trigger mail.

Keep the existing `send_interview_emails` command scheduled every five minutes.
It now sends all three categories. Failed recipients remain queued; successful
recipients are recorded individually. A crash after SMTP accepts a message but
before the database commits can still cause a duplicate on retry.
`ADMIN_NOTIFICATION_EMAIL`, when set, remains an additional recipient for every
category; unset it if all recipients should be managed by subscriptions.

Before production, apply migrations and configure SMTP as above. Run:

```sh
python manage.py test backoffice
python manage.py migrate --settings=portfolio_site.production
python manage.py test_notification_email your-test-address@example.com --settings=portfolio_site.production
```

The test command verifies SMTP acceptance. Confirm the message arrives in the
inbox, then test a subscribed member with a new job, an application stage change,
and an interview change, running the queue command after each save. Check an
unsubscribed account receives none. Do this before switching production traffic.

### Dashboard widgets

Each widget links to its underlying application or visitor list; active
applications opens a filtered list. Drag **Move widget** to reorder, or focus
that button and use Left/Right arrows. Drag the bottom-right resize corner to
change width and height. Layout is saved per user in the current browser.
**Reset widget layout** restores defaults. New widgets can use the same
`dashboard-widget` class and a stable unique `data-widget` identifier.
