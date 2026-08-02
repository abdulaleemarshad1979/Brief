# Brief - Daily Morning Briefing

A free Python automation that emails:

- World news
- India news
- Andhra Pradesh and Rajahmundry news
- Technology, AI and cybersecurity news
- Trending Hacker News stories
- Today's local weather

It runs daily with GitHub Actions and needs no paid server or paid API.

## 1. Create a GitHub repository

Create a **private** repository, then upload every file and folder from this project.

Keep the folder structure exactly as provided, including:

```text
.github/workflows/morning-briefing.yml
templates/briefing.html
```

## 2. Create a Gmail App Password

1. Open your Google Account.
2. Enable **2-Step Verification**.
3. Open **App passwords**.
4. Create an app password named `Morning Briefing`.
5. Copy the generated 16-character password.

Do not use your normal Gmail password.

## 3. Add GitHub repository secrets

Open:

```text
Repository → Settings → Secrets and variables → Actions
```

Create these three repository secrets:

| Secret | Value |
|---|---|
| `EMAIL_ADDRESS` | Gmail address that sends the briefing |
| `EMAIL_APP_PASSWORD` | 16-character Google App Password |
| `RECIPIENT_EMAIL` | Address that receives the briefing |

The sender and recipient can be the same Gmail address.

## 4. Test it immediately

Open:

```text
Repository → Actions → Daily Morning Briefing → Run workflow
```

Within a minute or two, check your inbox and Spam folder.

## 5. Daily schedule

The included workflow runs every day at:

```text
6:30 AM Asia/Kolkata
```

To change it, edit:

```yaml
- cron: "30 6 * * *"
  timezone: "Asia/Kolkata"
```

Examples:

```text
6:00 AM → 0 6 * * *
7:00 AM → 0 7 * * *
7:30 AM → 30 7 * * *
```

## Run locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Set environment variables, then run:

```bash
python main.py
```

On PowerShell:

```powershell
$env:EMAIL_ADDRESS="youraddress@gmail.com"
$env:EMAIL_APP_PASSWORD="your-16-character-app-password"
$env:RECIPIENT_EMAIL="youraddress@gmail.com"
python main.py
```

## Customization

Edit `.github/workflows/morning-briefing.yml` to change:

- Name
- City
- Coordinates
- Timezone
- Delivery time

Edit `config.py` to change the number of stories in each section.

## Security

- Keep the repository private.
- Never commit your Gmail password or App Password.
- Store credentials only in GitHub Actions Secrets.
- Revoke the App Password from your Google Account if it is ever exposed.
