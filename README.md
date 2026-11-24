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

### Offered salary on applications

Add or edit an application to enter the optional **Salary offered**, including
currency, range and pay period. It appears first under **Job details** on the
application detail page. Job posting and company website links open in a new tab.
Apply migration `0012_application_salary_offered` with `python manage.py migrate`
locally before testing. After local approval, use the existing production
deployment process and run `python manage.py migrate --settings=portfolio_site.production`
before restarting the app.

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
using another browser can result in a new count. After the updated analytics consent is accepted, visitor records also store the
public IP address, last visit time, and total tracked page visits. Earlier
records remain without an IP until that browser returns and consents.

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

### Dashboard links

The dashboard retains its original layout. Click a number to open the associated
visitor or application list. Active applications opens a filtered list; country
and region counts open the matching visitors.


### IP geolocation and live visitor map

The approved dashboard layout is retained. Click **Visitors by country**, or
**Visitor world map** in the admin menu, to open the interactive world map.
Hover, tap, or keyboard-focus a country to see its unique visitor and visit
counts; use its **View visitors** link for the filtered records. The map and
country table refresh every 15 seconds while visible. Raw IPs are available
only in the permission-protected visitor admin; map JSON contains aggregates.

Install updated requirements and apply migrations. For direct connections,
Django takes the public address from `REMOTE_ADDR`, ignoring forwarded headers.
Behind Cloudflare, set `PORTFOLIO_TRUST_GEO_HEADERS=1` **only** when Cloudflare
overwrites the geo/IP headers and direct access to the origin is blocked.
This enables `CF-Connecting-IP`, `CF-IPCountry`, and optional `CF-Region`.
For other proxies, configure the server to supply the correct `REMOTE_ADDR`.

For local IP-to-country lookup, download a licensed GeoLite2 Country or City
MMDB from MaxMind and set `GEOIP_DATABASE_PATH` to its absolute server path.
Keep the database current using MaxMind's update tooling. IP addresses are
looked up locally and are not sent to an external geolocation service.
Without trusted country headers or a working MMDB, location stays Unknown.
Private/loopback addresses are not stored. VPN/proxy locations may differ from
a visitor's actual country. The map uses bundled Natural Earth public-domain
country outlines; no third-party map requests are made in the browser.

The consent preference version has changed so existing visitors are asked again
before IP collection. Declining disables subsequent tracking. Existing historic
records are retained. Counts measure consenting browser cookies, not individuals:
five different consenting browsers located in GB count as five UK visitors;
repeat page loads add visits without adding unique visitors. Clearing cookies
can create another unique record. Counts represent the latest known location
of each browser. Deploy this update only with the matching consent text.


### Fix Unknown countries without Cloudflare or a MaxMind account

Run in the activated production Python environment, with the production
application variables available:

```sh
python -m pip install -r requirements.txt
python manage.py update_geoip --settings=portfolio_site.production
python manage.py resolve_visitor_countries --settings=portfolio_site.production
```

Restart the cPanel Python app, then refresh Visitors and the map. The installer
puts DB-IP Country Lite at `var/geoip-country.mmdb` by default. A custom
`GEOIP_DATABASE_PATH` overrides this location; use the same setting in the
terminal and web app. The directory must be writable for the updater and
readable by the web app. The download needs outbound HTTPS. No visitor IPs
are sent to DB-IP: queries run against the downloaded database locally.

Run `update_geoip` monthly using cPanel cron and the same Python environment.
Downloads are validated before atomic replacement; a failed download leaves
the previous database intact. The backfill fills only missing countries and
does not increase visits or overwrite known countries. DB-IP Country Lite
provides country only; region can stay blank. Local data is ignored by Git
and must be installed separately on each server. Attribution appears in admin.
DB-IP data: https://db-ip.com/db/download/ip-to-country-lite (CC BY 4.0).


### Upcoming interviews on the dashboard

The dashboard shows the next three future scheduled interviews, earliest first,
for members allowed to view/change applications. Closed applications and past
scheduled times are excluded on page load. Cards link to job details and show
employer, role, stage, work arrangement, location, and the full scheduled date
and time in Europe/Dublin. Relative labels refresh every 30 seconds in the
browser; reload the dashboard to fetch newly scheduled or rescheduled interviews.
Motion follows the browser's reduced-motion preference. No migration is needed.

### Interview question documents

Open Admin → Interview questions, or use the dashboard panel to add or view
entries. Each entry stores the employer, interview date, and one private PDF or
DOCX attachment (up to 5 MB). Documents are stored in the database, not in the
public media directory, and downloads require an authenticated admin account
with permission to view or change interview questions. Uploading a new file
while editing replaces the existing attachment. Use the eye icon in the
dashboard or list to preview PDFs and DOCX files in a read-only modal; DOCX
previews are rendered locally and do not send private documents to an external
viewer.

Apply the new migration locally with `python manage.py migrate`. To deploy
manually, first push and pull the code on the production server, activate the
production Python environment, and run:

```sh
python manage.py check --settings=portfolio_site.production
python manage.py migrate --noinput --settings=portfolio_site.production
```

Back up the production database before applying migrations. The configured
GitHub Actions deployment also runs migrations automatically after a successful
deployment. Restart the Python app after a manual deployment, then check Admin
→ Interview questions.

### Private daily learnings

Open Admin → Learnings. Each staff account has its own private journal, with
1–10 heading/explanation cards per day. Leaving a field saves a database draft;
Save today's learning finalizes the whole entry. Draft changes remain separate
from the finalized version until saved. Today's entry can be updated; past dates
are read-only, including unfinished drafts. Dates follow Europe/Dublin.

The dashboard measures finalized learning days / elapsed calendar days this
month (including today), with full calendar length for historical months.
Green means 100%, yellow 75–99%, orange 40–74%, and red below 40%. Multiple
ideas or repeated saves never count a day twice. No public route exposes notes.

Deployment: run `python manage.py migrate --settings=portfolio_site.production`
and collect static assets with the existing deployment process, then restart
the app. The new migration is `backoffice.0010_learningentry`.
Verification: `python manage.py test backoffice --noinput`.

### Admin Logs

Superusers can open Admin → Logs for a terminal-style event viewer with category,
severity and search filters. It refreshes every five seconds and shows the latest
500 matching events. Events are stored in `backoffice_appevent` starting with
this release; old cPanel/PuTTY/server log files are not imported. Existing Django
admin history is retained separately. Passwords, form contents, query strings,
email addresses and raw exception messages are omitted from these events.
Errors show exception type and code location; hosting error logs may provide
additional debugging detail. The viewer is read-only and restricted to superusers.

Includes admin requests and model create/change/delete events, authentication,
learning drafts/saves, email queue creation, sender runs, missing subscriptions,
backend acceptance and failed deliveries. New jobs require the New jobs subscription;
application edits require Application updates. The scheduled `send_interview_emails`
command is still required; queueing alone does not send email. SMTP acceptance
is not inbox confirmation. Console/locmem acceptance is not real delivery.

Deploy migration `0011_appevent`, update static assets and restart the Python app.
Event storage is persistent; arrange database retention/backups with hosting operations.
