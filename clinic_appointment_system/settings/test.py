
from .base import *

SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = False
ALLOWED_HOSTS = ["*"]

# for testing, we use an in-memory SQLite database to avoid creating a physical file.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# password hashing is set to MD5 for faster tests, as security is not a concern in the test environment.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
# outbox for email and sms messages sent during tests, without really sending.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
DEFAULT_FROM_EMAIL = "test@medapp.local"
SMS_BACKEND = "sms.backends.locmem.LocmemBackend"

# media files are stored in a temporary directory during tests to avoid cluttering the project directory with test files.
import tempfile
MEDIA_ROOT = tempfile.mkdtemp(prefix="medapp_test_media_")

# celery settings for testing; tasks are executed eagerly to simplify testing and avoid the need for a running celery worker.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "clinic-appointment-test",
    }
}