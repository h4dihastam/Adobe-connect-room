# Adobe Connect Room Creator

یک سرویس Flask آماده Deploy روی Render برای ساخت روم Adobe Connect با Adobe Connect XML Web Services API.

## ساختار پروژه

```text
project/
├── app.py
├── requirements.txt
├── Procfile
├── render.yaml
└── .env.example
```

## Endpointها

| مسیر | توضیح |
| --- | --- |
| `/` | تست سریع بالا بودن سرور. |
| `/health` | پاسخ JSON برای Health Check. |
| `/create-room` | ساخت روم Adobe Connect. |

## تنظیمات محیطی

قبل از اجرا یا Deploy این متغیرها را تنظیم کن:

| Variable | Description |
| --- | --- |
| `AC_BASE_URL` | آدرس Adobe Connect، مثل `https://yourdomain.adobeconnect.com`. |
| `AC_USER` | کاربری که اجازه ساخت Meeting دارد. |
| `AC_PASS` | رمز عبور کاربر Adobe Connect. |
| `AC_FOLDER_ID` | شناسه SCO فولدر Meetings که روم‌ها داخل آن ساخته می‌شوند. |

نمونه:

```bash
cp .env.example .env
```

> فایل `.env` و اطلاعات واقعی ورود را داخل Git نگذار.

## اجرای لوکال

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export AC_BASE_URL="https://yourdomain.adobeconnect.com"
export AC_USER="admin@example.com"
export AC_PASS="your-password"
export AC_FOLDER_ID="12345"
flask --app app run
```

تست سرور:

```bash
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/health
```

## اجرای Production / Render

Render باید برنامه را با Gunicorn اجرا کند، نه با دستورهای Django مثل `gunicorn your_application.wsgi`.

### Build Command

```bash
pip install -r requirements.txt
```

### Start Command

```bash
gunicorn app:app
```

معنی `gunicorn app:app`:

- `app` اول: نام فایل `app.py`
- `app` دوم: نام Flask instance داخل فایل

همین دستور داخل `Procfile` هم قرار داده شده است:

```Procfile
web: gunicorn app:app
```

و فایل `render.yaml` هم برای Deploy تمیزتر اضافه شده است.

## ساخت روم Adobe Connect

```bash
curl -X POST "https://YOUR-RENDER-APP.onrender.com/create-room?access=protected" \
  -H "Content-Type: application/json" \
  -d '{"name":"hangout demo"}'
```

نمونه پاسخ موفق:

```json
{
  "name": "hangout demo",
  "room": "https://yourdomain.adobeconnect.com/hangout-demo/",
  "sco_id": "2007184134",
  "url_path": "/hangout-demo/"
}
```

`access` می‌تواند یکی از این مقدارها باشد:

- `public`: هر کسی با لینک بتواند وارد شود.
- `protected`: کاربران ثبت‌شده و مهمان‌های پذیرفته‌شده بتوانند وارد شوند.
- `private`: فقط کاربران/شرکت‌کننده‌های تعریف‌شده بتوانند وارد شوند.

## نکات مهم Render

- `gunicorn` حتماً باید داخل `requirements.txt` باشد.
- اگر نام فایل را از `app.py` به `main.py` تغییر دادی، Start Command باید بشود: `gunicorn main:app`.
- پورت را دستی تنظیم نکن؛ Render خودش متغیر `PORT` را می‌دهد و فایل `app.py` برای اجرای مستقیم هم با `PORT` سازگار است.
