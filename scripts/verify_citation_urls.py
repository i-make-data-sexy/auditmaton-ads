# verify_citation_urls.py
# Citation-URL health check for audit JSON content.
#
# Walks a json/ subtree, extracts every external http(s) URL from the content
# fields, and classifies each one:
#   ok        - resolved (2xx/3xx)
#   broken    - a real link fault (4xx/5xx, excluding 429)
#   throttled - HTTP 429; reflects the requester's IP, not the link
#   error     - could not connect (DNS, SSL/cert, timeout); NOT a link fault
#
# Only "broken" fails the run (exit 1). "throttled" and "error" are reported
# but do not fail, because both reflect the local machine/network rather than
# the link itself. A wall of "error" usually means Python cannot verify TLS
# certs (on macOS run the bundled "Install Certificates.command", or just use
# the requests path below, which uses certifi).
#
# Usage:
#   python3 scripts/verify_citation_urls.py                  # checks json/
#   python3 scripts/verify_citation_urls.py json/meta-ads    # one platform
#   python3 scripts/verify_citation_urls.py json/meta-ads --delay 2.0

import sys
import re
import json
import glob
import time
import argparse

URL_RE = re.compile(r"https?://[^\s'\"<>)]+")

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def collect_strings(obj):
    """
    Yields every string value found anywhere in a nested JSON structure.

    Args:
        obj: A parsed JSON value (dict, list, str, or scalar)

    Yields:
        str: Each string value in the structure
    """
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from collect_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from collect_strings(v)


def extract_urls(root):
    """
    Extracts every unique external URL from the JSON files under root.

    Args:
        root (str): Directory to walk for .json files

    Returns:
        list: Sorted unique URLs found in the content
    """
    urls = set()
    for path in glob.glob(f"{root}/**/*.json", recursive=True):
        # Skip registry and schema helper files
        if "/_" in path:
            continue
        try:
            data = json.load(open(path, encoding="utf-8"))
        except (ValueError, OSError):
            continue
        for s in collect_strings(data):
            for m in URL_RE.findall(s):
                urls.add(m.rstrip(".,);"))
    return sorted(urls)


def _check_requests(url, timeout):
    """
    Fetches a URL with the requests library (uses certifi for TLS).

    Args:
        url (str): The URL to check
        timeout (int): Per-request timeout in seconds

    Returns:
        tuple: (kind, detail) where kind is ok/broken/throttled/error
    """
    import requests

    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout, allow_redirects=True)
        return _classify(r.status_code)
    except requests.exceptions.RequestException as e:
        return ("error", type(e).__name__)


def _check_urllib(url, timeout):
    """
    Fetches a URL with urllib, building a TLS context from certifi if present.

    Args:
        url (str): The URL to check
        timeout (int): Per-request timeout in seconds

    Returns:
        tuple: (kind, detail) where kind is ok/broken/throttled/error
    """
    import ssl
    import urllib.request
    import urllib.error

    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        # No certifi: fall back to an unverified context so a missing local
        # cert bundle does not masquerade as a broken link.
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return _classify(resp.status)
    except urllib.error.HTTPError as e:
        return _classify(e.code)
    except Exception as e:
        return ("error", type(e).__name__)


def _classify(code):
    """
    Maps an HTTP status code to a health category.

    Args:
        code (int): The HTTP status code

    Returns:
        tuple: (kind, code) where kind is ok/broken/throttled
    """
    if code == 429:
        return ("throttled", code)
    if 200 <= code < 400:
        return ("ok", code)
    return ("broken", code)


def check(url, timeout=20):
    """
    Fetches a URL and returns its health category, preferring requests.

    Args:
        url (str): The URL to check
        timeout (int): Per-request timeout in seconds

    Returns:
        tuple: (kind, detail) where kind is ok/broken/throttled/error
    """
    try:
        import requests  # noqa: F401
        return _check_requests(url, timeout)
    except ImportError:
        return _check_urllib(url, timeout)


def main():
    parser = argparse.ArgumentParser(description="Verify citation URLs in audit JSON.")
    parser.add_argument("root", nargs="?", default="json", help="Directory to scan (default: json)")
    parser.add_argument("--delay", type=float, default=1.5, help="Seconds between requests")
    args = parser.parse_args()

    urls = extract_urls(args.root)
    print(f"{len(urls)} unique URLs under {args.root}/\n")

    ok = 0
    broken = []
    throttled = []
    errors = []
    for u in urls:
        kind, detail = check(u)
        if kind == "ok":
            ok += 1
        elif kind == "throttled":
            throttled.append(u)
            print(f"  429 throttled (not a link fault)  {u}")
        elif kind == "error":
            errors.append((detail, u))
            print(f"  ERROR {detail} (could not connect)  {u}")
        else:
            broken.append((detail, u))
            print(f"  {detail} BROKEN  {u}")
        time.sleep(args.delay)

    print(f"\nsummary: ok={ok}  broken={len(broken)}  throttled={len(throttled)}  error={len(errors)}")
    if errors and ok == 0 and not broken:
        print("note: every request errored, which almost always means Python "
              "cannot verify TLS certificates. Run macOS 'Install "
              "Certificates.command', or `pip install requests certifi`, then re-run.")
    if throttled:
        print("note: throttling reflects this machine's IP, not the links.")
    sys.exit(1 if broken else 0)


if __name__ == "__main__":
    main()
