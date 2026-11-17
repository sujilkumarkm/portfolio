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
