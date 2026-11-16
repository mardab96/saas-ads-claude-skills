"""Shared parsing for the saas-ads helpers. Standard library only.

num():        "1,200.50", "$1,200.50", "EUR 500", "500 zl", "PLN 500" all parse.
              Commas must be thousands separators, so a European decimal comma
              ("1.200,50") is rejected instead of misread. With
              decimal_comma=True (the --decimal-comma flag) the reverse holds:
              "1.200,50" and "1200,50" parse, and a dot may only group
              thousands.
frac():       like num(), and "20%" parses as 0.2.
parse_day():  "2026-11-01", "2026-11-01 09:30", "2026-11-01 09:30:15",
              "2026-11-01T09:30:15Z" all parse. Time of day is validated and
              then dropped, so ages are counted in whole days. MM/DD/YYYY
              parses only with us=True (the --us-dates flag).
read_table(): reads a CSV with a comma or semicolon delimiter, lower-cases
              headers, trims them, turns spaces into underscores, and drops a
              trailing unit in brackets, so "Spend (USD)" reads as spend. When a
              required column is missing, one export synonym is used instead:
              cost, amount_spent -> spend; campaign_name -> campaign;
              channel_name -> channel. A column that already has the required
              name always wins. Every renamed header prints a header_mapping
              line on stderr, so a CSV on stdout stays clean. A missing column
              error lists the headers that were found.
              The result is a list of dicts that also carries the detected
              delimiter.
money_mode(): True when --decimal-comma was passed, or when the file uses a
              semicolon delimiter and a money cell looks like 1.200,50.
name_or_unattributed(): a blank channel or campaign becomes "unattributed".
t26_line():   the T26 note when unattributed customers are 10% or more.
parse_pools():  --pool name=a,b specs, with the T24 checks.
"""
import csv
import datetime
import io
import os
import sys
import re

_CODES = re.compile(r"(PLN|USD|EUR|GBP)", re.IGNORECASE)
_SYMBOLS = ("$", "\u20ac", "\u00a3", "z\u0142", "Z\u0141")
_SPACES = re.compile(r"[\s\u00a0\u202f]+")
_GROUPED = re.compile(r"^\d{1,3}(,\d{3})+(\.\d+)?$")
_PLAIN = re.compile(r"^(\d+(\.\d*)?|\.\d+)$")
_EU_FORMS = re.compile(r"^(\d{1,3}(\.\d{3})+(,\d+)?|\d+,\d+)$")
_EU_MONEY = re.compile(r"^\d{1,3}(\.\d{3})*,\d{2}$")
_TIME = r"(\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?)(?:Z|[+-]\d{2}:?\d{2})?"
_STAMP = re.compile(r"^(\d{4}-\d{2}-\d{2})(?:[ T]" + _TIME + r")?$")
_US = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})(?:[ T]" + _TIME + r")?$")

UNATTRIBUTED = "unattributed"
T26_SHARE = 0.10  # T26, share of paying customers
T26_TEXT = (
    "unattributed customers are at least 10% of the total, so they can change a channel ranking. "
    "Start capturing the campaign at signup."
)


class Table(list):
    """Rows from read_table. The delimiter attribute holds the one that was detected."""

    delimiter = ","


def _strip_money(value):
    text = "" if value is None else str(value)
    text = _CODES.sub("", text)
    for symbol in _SYMBOLS:
        text = text.replace(symbol, "")
    return _SPACES.sub("", text)


def num(value, decimal_comma=False):
    """Return a finite, non-negative float or raise ValueError."""
    text = _strip_money(value)
    if decimal_comma and ("," in text or "." in text):
        if not _EU_FORMS.match(text):
            raise ValueError("with --decimal-comma use 1.200,50 or 1200,50, got %r" % str(value))
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        if not _GROUPED.match(text):
            raise ValueError(
                "comma must be a thousands separator, got %r; rerun with --decimal-comma if this file writes decimals with a comma"
                % str(value)
            )
        text = text.replace(",", "")
    if not _PLAIN.match(text):
        raise ValueError("not a non-negative number: %r" % str(value))
    return float(text)


def frac(value, decimal_comma=False):
    """Return a fraction. A trailing percent sign divides by 100."""
    text = ("" if value is None else str(value)).strip()
    if text.endswith("%"):
        return num(text[:-1], decimal_comma) / 100
    return num(text, decimal_comma)


def parse_day(value, us=False):
    """Return a datetime.date from YYYY-MM-DD, or MM/DD/YYYY when us is true."""
    text = "" if value is None else str(value).strip()
    match = _US.match(text)
    if match:
        if not us:
            raise ValueError(
                "date %r is not YYYY-MM-DD; convert it, or rerun with --us-dates if it is MM/DD/YYYY" % text
            )
        month, day, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        text = "%04d-%02d-%02d" % (year, month, day) + (" " + match.group(4) if match.group(4) else "")
    match = _STAMP.match(text)
    if not match:
        raise ValueError(
            "date must be YYYY-MM-DD, optionally followed by HH:MM or HH:MM:SS "
            "after a space or T, got %r" % text
        )
    day = datetime.date.fromisoformat(match.group(1))
    if match.group(2):
        parts = [int(float(part)) for part in match.group(2).split(":")]
        datetime.time(parts[0], parts[1], parts[2] if len(parts) > 2 else 0)
    return day


_UNIT = re.compile(r"\s*[\(\[][^)\]]*[\)\]]\s*$")
ALIASES = {
    "cost": "spend",
    "amount_spent": "spend",
    "campaign_name": "campaign",
    "channel_name": "channel",
}


def _squash(text):
    return re.sub(r"\s+", "_", (text or "").replace("\ufeff", "").strip().lower())


def normalise_header(text):
    """Lower-case, trim, turn spaces into underscores, and drop a trailing unit such as (USD)."""
    return _squash(_UNIT.sub("", (text or "").replace("\ufeff", "").strip()))


def read_table(path, required):
    """Return rows as dicts keyed by normalised header. Raise ValueError with the headers found."""
    with open(path, newline="", encoding="utf-8-sig") as handle:
        text = handle.read()
    lines = text.splitlines()
    first = lines[0] if lines else ""
    delimiter = ";" if first.count(";") > first.count(",") else ","
    raw = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    if not raw:
        raise ValueError("%s: no data rows" % path)
    header = [normalise_header(cell) for cell in raw[0]]
    renamed = {i for i, cell in enumerate(raw[0]) if header[i] != _squash(cell)}
    for target in required:
        if target in header:
            continue
        for i, name in enumerate(header):
            if ALIASES.get(name) == target:
                header[i] = target
                renamed.add(i)
                break
    if not set(required) <= set(header):
        raise ValueError(
            "required columns: %s; headers found: %s" % (", ".join(required), ", ".join(h for h in header if h) or "none")
        )
    if renamed:
        pairs = "; ".join("%s -> %s" % (raw[0][i].replace("\ufeff", "").strip(), header[i]) for i in sorted(renamed))
        print("header_mapping:\t%s: %s" % (os.path.basename(path), pairs), file=sys.stderr)
    rows = Table()
    rows.delimiter = delimiter
    for cells in raw[1:]:
        if not any(cell.strip() for cell in cells):
            continue
        cells = cells + [""] * (len(header) - len(cells))
        rows.append(dict(zip(header, cells)))
    if not rows:
        raise ValueError("%s: no data rows" % path)
    return rows


def money_mode(table, flag, columns):
    """Return True when money cells use a decimal comma: the flag, or a semicolon file with a 1.200,50 style cell."""
    if flag:
        return True
    if getattr(table, "delimiter", ",") != ";":
        return False
    return any(_EU_MONEY.match(_strip_money(row.get(column))) for row in table for column in columns)


def name_or_unattributed(value):
    """Blank channel or campaign names become unattributed (T26)."""
    text = (value or "").strip()
    return UNATTRIBUTED if not text or text.lower() == UNATTRIBUTED else text


def t26_line(unattributed, total):
    """Return the T26 note line when unattributed customers are at least 10% of the total, else None."""
    if total and unattributed / total >= T26_SHARE:
        return "T26:\t" + T26_TEXT
    return None


def segment_of(name):
    lowered = name.lower()
    if re.search(r"non[_\s-]?brand", lowered):
        return "non_brand"
    if "brand" in lowered:
        return "brand"
    return "other"


def platform_of(name):
    return re.split(r"[_\s-]+", name.strip().lower())[0]


def parse_pools(specs):
    """Return {member: pool name}. Enforce T24: no brand with non-brand, no cross-platform pool."""
    members_to_pool = {}
    for spec in specs or []:
        name, sep, rest = spec.partition("=")
        name = name.strip()
        members = [m.strip() for m in rest.split(",") if m.strip()]
        if not sep or not name or len(members) < 2:
            raise ValueError("--pool needs name=first,second (at least two members), got %r" % spec)
        if {segment_of(m) for m in members} >= {"brand", "non_brand"}:
            raise ValueError("never pool brand with non-brand (T24): %s" % spec)
        if len({platform_of(m) for m in members}) > 1:
            raise ValueError(
                "never pool across platforms (T24): %s. Members must start with the same platform word, such as google_ or meta_" % spec
            )
        for member in members:
            if member in members_to_pool:
                raise ValueError("%s is in two pools" % member)
            members_to_pool[member] = name
    return members_to_pool


def check_pool_members(pools, found):
    missing = sorted(m for m in pools if m not in set(found))
    if missing:
        raise ValueError("pool member not found in the file: %s; names found: %s" % (", ".join(missing), ", ".join(sorted(set(found)))))
