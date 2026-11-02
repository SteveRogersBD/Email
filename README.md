# Recruiter Outreach Tool

A local Streamlit app for sending personalized, one-at-a-time recruiter outreach emails through the Gmail API. It stores templates, settings, and confirmed send history in lightweight local text files.

## Features

- Gmail OAuth 2.0 for a local desktop app with the minimal `gmail.send` scope.
- Jinja2 templates with safe handling for missing optional variables.
- Plain-text and HTML MIME alternatives with clickable links.
- Default PDF resume plus a per-email replacement picker.
- Editable starter templates for recruiter, founder, and follow-up outreach.
- Text-file send records with status, Gmail message ID, and error details for local auditability.
- No bulk sending, open tracking, reply tracking, or automatic sequences.

## 1. Create a virtual environment

From this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run the command in a terminal where local scripts are allowed, or use the virtual environment's Python directly.

## 2. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 3. Configure Google Cloud

1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project, or select a personal project.
3. In **APIs & Services → Library**, enable **Gmail API**.
4. Open **APIs & Services → OAuth consent screen**.
5. Choose **External** for a personal Gmail account, enter an app name and support email, and add yourself as a test user if the app is in testing mode.
6. Under **APIs & Services → Credentials**, choose **Create Credentials → OAuth client ID**.
7. Select **Desktop app**, create the client, and download the JSON file.
8. Rename the downloaded file to `credentials.json` and place it in this project directory.

The app requests only `https://www.googleapis.com/auth/gmail.send`. It does not ask for or store your Gmail password. After the first login, Google stores an OAuth token in the local ignored file `token.json`; the token is refreshed automatically when possible.

If Google shows an unverified-app warning during personal testing, use the advanced option to continue only if you recognize the local app you created. Keep the OAuth client and token files private.

## 4. Optional environment configuration

Copy `.env.example` to `.env` if you want to override defaults:

```powershell
Copy-Item .env.example .env
```

The defaults use `uploads/`, `credentials.json`, and `token.json` in this project directory. Runtime data is stored in the ignored root-level files `email_templates.txt`, `app_settings.txt`, and `outreach_history.txt`. `.env`, OAuth credentials, tokens, local data files, and uploaded files are ignored by Git.

## 5. Run the app

```powershell
python -m streamlit run app.py
```

Open the local URL Streamlit prints, usually `http://localhost:8501`.

The app opens on **Compose**. Use **Settings → Connect Gmail** for the first OAuth login. The browser redirect is handled by the local Google OAuth flow.

## 6. Send a test email to yourself

1. Connect Gmail in **Settings**.
2. Save your name, signature, and profile links.
3. Upload a PDF under **Default resume** if desired.
4. Open **Compose**, enter your own email address, and choose a starter template.
5. Review the rendered preview and attachment name.
6. Click **Send email** once and wait for Gmail confirmation.
7. The confirmed `sent` status and Gmail message ID are saved locally in `outreach_history.txt`.

The app does not automatically retry a timed-out Gmail request because the outcome could be unknown and a retry might duplicate the email.

## 7. Template variables

Templates use Jinja syntax. Available variables include:

```text
recipient_email
recipient_name
company
job_title
full_name
signature
linkedin_url
github_url
portfolio_url
```

For optional fields, use a fallback such as `{{ company or 'your company' }}`. Templates can be edited in the app or in the starter `.md` files in the project root. Each sent email contains both a readable plain-text version and an HTML version.

## 8. Tests and checks

```powershell
python -m pytest -q
python -m compileall -q .
```

The three starter templates and local text files are initialized automatically on app startup.

## Troubleshooting

### `credentials.json` not found

Download the Desktop OAuth client JSON from Google Cloud and place it at `credentials.json` beside `app.py`. If you use a different filename, set `GOOGLE_CLIENT_SECRET_FILE` in `.env`.

### `redirect_uri_mismatch`

Use an OAuth client of type **Desktop app**, not a Web application client. Delete the local `token.json` after changing OAuth clients, then connect again.

### `access_denied` or the app is blocked

Confirm that your Google account is listed as a test user on the OAuth consent screen. Confirm that Gmail API is enabled in the same Google Cloud project as the OAuth client.

### Gmail scope or consent problems

Delete `token.json` and reconnect so Google can show a fresh consent screen. The app only needs Gmail send permission.

### Resume attachment errors

Only existing PDF files under the configured size limit are accepted. Re-upload the file in Settings or choose a different PDF on Compose. The app refuses to send if a selected attachment is missing.

### A message shows `unknown`

The request timed out after reaching the send operation, so the app intentionally did not retry. Check Gmail Sent before deciding whether any manual follow-up is needed.

## Project layout

```text
app.py
config.py
services/
  gmail_service.py
  outreach_service.py
  template_service.py
utils/
  email_builder.py
  validators.py
pages/
  templates.py
  history.py
  settings.py
tests/
data/
uploads/
```
