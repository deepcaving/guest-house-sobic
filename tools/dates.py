"""Compute the live "Preferred dates" example, one month ahead.

The enquiry form shows an example date range so a guest knows what kind of
value to type. It must always point FORWARD - never at a month that has
already passed - so it is computed from the current date instead of being
written by hand.

This is the Python twin of dates.js. The two must agree: dates.js computes
the placeholder in the browser, this computes the static fallback that goes
into index.html for anyone whose JavaScript does not run.

The example range is the 10th to the 17th of the month AFTER the current
month, so it reads as "book me for soon" rather than "the season is over".
The day is clamped to the length of the target month, so the 31st of a
30-day month still yields a valid range.
"""

from datetime import date

MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"],
    "de": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
           "August", "September", "Oktober", "November", "Dezember"],
    "bs": ["januar", "februar", "mart", "april", "maj", "juni", "juli",
           "august", "septembar", "oktobar", "novembar", "decembar"],
    "it": ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
           "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"],
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre"],
    "nl": ["januari", "februari", "maart", "april", "mei", "juni", "juli",
           "augustus", "september", "oktober", "november", "december"],
}

DAY_FROM = 10
DAY_TO = 17


def days_in_month(year, month):
    """Number of days in a 1-based month (1 = January)."""
    if month == 12:
        return 31
    # First day of the NEXT month, minus one day.
    nxt = date(year + (1 if month == 12 else 0), 1 if month == 12 else month + 1, 1)
    return (nxt - date(year, month, 1)).days


def target_month(today=None):
    """The month AFTER the current one, as (year, 1-based month)."""
    today = today or date.today()
    year, month = today.year, today.month + 1
    if month > 12:
        month = 1
        year += 1
    return year, month


def example_range(lang="en", today=None):
    """The example date range as a dict: d1, d2, month (name), year."""
    year, month = target_month(today)
    last = days_in_month(year, month)
    names = MONTHS.get(lang, MONTHS["en"])
    return {
        "d1": min(DAY_FROM, last),
        "d2": min(DAY_TO, last),
        "month": names[month - 1],
        "year": year,
        "year_short": str(year)[2:],
    }


def fill(template, lang="en", today=None):
    """Substitute the placeholders into a template string."""
    if not template or "{{" not in template:
        return template or ""
    r = example_range(lang, today)
    out = template
    for key, value in (("{{d1}}", r["d1"]), ("{{d2}}", r["d2"]),
                       ("{{month}}", r["month"]), ("{{year}}", r["year"]),
                       ("{{yearShort}}", r["year_short"])):
        out = out.replace(key, str(value))
    return out


def english_example(today=None):
    """The English example date range as a plain string, e.g.
    'e.g. 10-17 December 2026'. Used for the static fallback."""
    r = example_range("en", today)
    return f"e.g. {r['d1']}\u2013{r['d2']} {r['month']} {r['year']}"
