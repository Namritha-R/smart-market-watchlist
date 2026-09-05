from datetime import datetime, timezone


MAX_DATA_AGE_SECONDS = 60


def is_stale(timestamp):
    now = datetime.now(timezone.utc)

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    age = (now - timestamp).total_seconds()

    return age > MAX_DATA_AGE_SECONDS