# سیستم نوبت‌دهی آنلاین پزشکان

 برای مدیریت و رزرو آنلاین نوبت‌های ویزیت پزشکان، با معماری MVT جنگو.

نمودار ERD در فایل `ERD.png` موجود است.

## امکانات

🔹 ثبت‌نام و ورود با شماره تلفن یا ایمیل<br>
🔹 ورود سریع با کد یکبار مصرف (پیش‌فرض، بدون رمز عبور) یا با رمز عبور، برای بیمار و پزشک<br>
🔹 ورود با حساب گوگل برای بیماران<br>
🔹 صفحه‌ی ورود جداگانه برای پزشکان<br>
🔹 پروفایل کاربری با آواتار قابل‌تنظیم و تاریخ تولد شمسی برای بیماران<br>
🔹 ساخت حساب پزشک از پنل ادمین، شامل تخصص، شماره نظام پزشکی و هزینه‌ی ویزیت<br>
🔹 تعریف ساعات کاری پزشک و تولید خودکار نوبت‌های خالی<br>
🔹 جستجوی پزشک بر اساس نام یا تخصص<br>
🔹 رزرو و لغو نوبت با کسر و بازگشت خودکار از کیف‌پول<br>
🔹 ثبت نظر و امتیاز بیمار برای پزشک<br>
🔹 نمایش تاریخ‌ها به شمسی در تمام صفحات<br>
🔹 ارسال پیامک با بک‌اند قابل‌تعویض (کنسول، Kavenegar)<br>
🔹 ارسال ایمیل برای تاییدیه‌ی رزرو، بازیابی رمز عبور و تغییر ایمیل<br>
🔹 پردازش ناهمگام با Celery برای ارسال پیام‌ها و پاک‌سازی دوره‌ای نوبت‌های منقضی<br>
🔹 دستور مدیریتی برای ساخت داده‌ی نمونه با Faker<br>
🔹 تست‌های خودکار با pytest<br>

## پشته‌ی فنی

<p align="center">
  <img src="https://img.shields.io/badge/Django-5.2-092E20?style=flat-square&logo=django&logoColor=white" alt="Django">
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/Celery-37814A?style=flat-square&logo=celery&logoColor=white" alt="Celery">
  <img src="https://img.shields.io/badge/Gunicorn-499848?style=flat-square&logo=gunicorn&logoColor=white" alt="Gunicorn">
  <img src="https://img.shields.io/badge/nginx-009639?style=flat-square&logo=nginx&logoColor=white" alt="nginx">
  <img src="https://img.shields.io/badge/Bootstrap-5-7952B3?style=flat-square&logo=bootstrap&logoColor=white" alt="Bootstrap">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white" alt="pytest">
</p>
<p align="center"><strong>django-allauth · WhiteNoise · jdatetime</strong></p>

## ساختار اپ‌ها

| اپ | مسئولیت |
|---|---|
| accounts | کاربر، احراز هویت، پروفایل |
| doctors | پزشک، تخصص، ساعات کاری، نوبت‌های خالی |
| patients | بیمار، نوبت‌های من |
| payments | کیف‌پول و تراکنش‌ها |
| appointments | رزرو و لغو نوبت |
| reviews | نظر و امتیاز |
| common | ابزارهای مشترک بین اپ‌ها |

## تنظیمات

تنظیمات پروژه در `clinic_appointment_system/settings/` به سه بخش تقسیم شده:

- `base.py`: تنظیمات مشترک
- `dev.py`: محیط توسعه، SQLite، ایمیل و پیامک در کنسول
- `test.py`: مخصوص اجرای تست‌ها
- `production.py`: محیط نهایی، PostgreSQL، HTTPS، ایمیل و پیامک واقعی

انتخاب محیط با متغیر `DJANGO_SETTINGS_MODULE` در فایل `env.` انجام می‌شود:

```
DJANGO_SETTINGS_MODULE=clinic_appointment_system.settings.dev
DJANGO_SETTINGS_MODULE=clinic_appointment_system.settings.production
```

در `docker-compose.yml` این مقدار همیشه روی production تنظیم شده است. در
صورت اجرای بدون Docker و نبود این متغیر، محیط dev فعال می‌شود.

توجه: در تنظیمات production، مقادیر `SECRET_KEY`، `ALLOWED_HOSTS` و اطلاعات
دیتابیس مقدار پیش‌فرض ندارند و باید در `env.` تعیین شوند.

## راه‌اندازی با Docker

```bash
cp .env.example .env
docker compose up --build
```

این دستور سرویس‌های db، redis، web، nginx، celery_worker و celery_beat را
اجرا می‌کند. برای ساخت کاربر ادمین:

```bash
docker compose exec web python manage.py createsuperuser
```

آدرس پروژه پس از اجرا: `http://localhost`

توجه: تنظیمات nginx فعلاً بدون گواهی SSL است. اگر `SECURE_SSL_REDIRECT`
روی True باشد و SSL واقعی پیکربندی نشده باشد، سایت بالا نمی‌آید. تا آماده
شدن SSL، این مقدار را False بگذارید.

## راه‌اندازی بدون Docker

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

برای اجرای کارهای ناهمگام (اختیاری در محیط توسعه):

```bash
celery -A clinic_appointment_system worker -l info
celery -A clinic_appointment_system beat -l info
```

## متغیرهای محیطی

توضیح کامل متغیرها در فایل `env.example.` آمده است. مهم‌ترین‌ها:

| متغیر | کاربرد |
|---|---|
| DJANGO_SETTINGS_MODULE | dev یا production انتخاب محیط|
| SECRET_KEY, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS |production تنظیمات امنیتی |
| USE_SQLITE, DB_* | تنظیمات دیتابیس |
| EMAIL_* | ارسال ایمیل واقعی |
| GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET | ورود با گوگل |
| SMS_BACKEND, SMS_API_KEY, SMS_SENDER_LINE | تنظیمات پیامک |
| REDIS_URL | و کش celery  برای  Redis آدرس  |

### ورود با گوگل

۱. در Google Cloud Console یک OAuth Client ID از نوع Web application بسازید.

۲. آدرس بازگشت (Redirect URI) را در همان صفحه ثبت کنید. مقدار آن این است:

   ```text
   https://YOUR-DOMAIN/social-auth/google/login/callback/
   ```

   به‌جای YOUR-DOMAIN دامنه‌ی خودتان را بگذارید.

۳. مقادیر GOOGLE_CLIENT_ID و GOOGLE_CLIENT_SECRET را در فایل `env.` قرار دهید.

### پیامک

بک‌اند پیامک با متغیر SMS_BACKEND قابل تغییر است:

| بک‌اند | کاربرد |
|---|---|
| sms.backends.console.ConsoleBackend | توسعه، چاپ در کنسول |
| sms.backends.locmem.LocmemBackend | تست خودکار |
| sms.backends.kavenegar.KavenegarBackend | پروداکشن |

برای افزودن پنل جدید، یک فایل مشابه در `sms/backends/` با متد send_message
ایجاد کنید.

## داده‌ی نمونه

```bash
python manage.py seed_demo_data
python manage.py seed_demo_data --specialties 8 --doctors 12 --patients 30 --appointments 40 --password Test1234
```

## ساخت حساب پزشک

حساب پزشک فقط از پنل ادمین ساخته می‌شود:

۱. وارد `/admin/` شوید و از بخش Doctors گزینه‌ی Add Doctor را انتخاب کنید.
۲. شماره تلفن، ایمیل، نام، تخصص، شماره نظام پزشکی و هزینه‌ی ویزیت را وارد
کنید. رمز عبور اختیاری است و در صورت خالی‌بودن به‌صورت خودکار ساخته می‌شود.
۳. اطلاعات ورود برای پزشک از طریق پیامک و ایمیل ارسال می‌شود.
۴. پزشک از آدرس `/doctors/login/` یا با کد یکبار مصرف از
`/doctors/login/otp/` وارد می‌شود.

## تست‌ها

```bash
pytest
pytest doctors/
pytest -v -k login
```

تنظیمات تست مستقل از محیط توسعه است و از پایگاه‌داده‌ی SQLite در حافظه
استفاده می‌کند؛ ایمیل و پیامک در این محیط ارسال واقعی ندارند.

## لایسنس

  
MIT - فایل لایسنس را ببینید
