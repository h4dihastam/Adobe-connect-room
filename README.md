# Adobe Connect Room Creator

A small Flask API that logs in to Adobe Connect and creates a meeting room through the Adobe Connect XML Web Services API.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set these environment variables before running the service:

| Variable | Description |
| --- | --- |
| `AC_BASE_URL` | Your Adobe Connect account URL, for example `https://yourdomain.adobeconnect.com`. |
| `AC_USER` | Adobe Connect user that can create meetings. |
| `AC_PASS` | Password for `AC_USER`. |
| `AC_FOLDER_ID` | Meeting folder SCO ID where rooms should be created. |

## Run

```bash
export AC_BASE_URL="https://yourdomain.adobeconnect.com"
export AC_USER="admin@example.com"
export AC_PASS="your-password"
export AC_FOLDER_ID="12345"
flask --app app run
```

## Create a room

```bash
curl -X POST "http://127.0.0.1:5000/create-room?access=protected" \
  -H "Content-Type: application/json" \
  -d '{"name":"hangout demo"}'
```

Successful response:

```json
{
  "name": "hangout demo",
  "room": "https://yourdomain.adobeconnect.com/hangout-demo/",
  "sco_id": "2007184134",
  "url_path": "/hangout-demo/"
}
```

`access` can be:

- `public`: anyone with the URL can enter.
- `protected`: registered users and accepted guests can enter.
- `private`: only registered users and participants can enter.

## Notes

- The service uses `sco-update` to create a meeting, then `permissions-update` to set public access behavior.
- Keep `.env` and real Adobe Connect credentials out of Git.
