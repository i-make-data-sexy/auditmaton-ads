# verify_citation_urls.py
# Citation-URL health check for audit JSON content.
#
# Walks a json/ subtree, extracts every external http(s) URL from the content
# fields, and reports any that do not resolve to a live page. Run it from a
# normal network (e.g., a laptop); datacenter/sandbox IPs get rate-limited
# (HTTP 429) or CAPTCHA-redirected by support.google.com, which looks like a
# failure but is not a broken link.
#
# Usage:
#   python3 scripts/verify_citation_urls.py                       # checks json/
#   python3 scripts/verify_citation_urls.py json/meta-ads         # one platform
#   python3 scripts/verify_citation_urls.py json/meta-ads --delay 2.0
#
# Exit code is 0 when nothing is broken, 1 when a real broken URL is found.
# A 429 (throttled) is reported separately and does NOT fail the run, since it
# reflects the requester's IP, not the link.

import sys
import re
import json
import glob
import time
import argparse
import urllib.request
import urllib.error

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


def check(url, timeout=20):
    """
    Fetches a URL and returns its final HTTP status after redirects.

    Args:
        url (str): The URL to check
        timeout (int): Per-request timeout in seconds

    Returns:
        int: The HTTP status code, or 0 if the request failed to connect
    """
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def main():
    parser = argparse.ArgumentParser(description="Verify citation URLs in audit JSON.")
    parser.add_argument("root", nargs="?", default="json", help="Directory to scan (default: json)")
    parser.add_argument("--delay", type=float, default=1.5, help="Seconds between requests")
    args = parser.parse_args()

    urls = extract_urls(args.root)
    print(f"{len(urls)} unique URLs under {args.root}/")

    broken = []
    throttled = []
    ok = 0
    for u in urls:
        st = check(u)
        if st == 200:
            ok += 1
        elif st == 429:
            throttled.append(u)
            print(f"  429 (throttled, not a link fault)  {u}")
        else:
            broken.append((st, u))
            print(f"  {st} (BROKEN)  {u}")
        time.sleep(args.delay)

    print(f"\nsummary: 200={ok}  broken={len(broken)}  throttled={len(throttled)}")
    if throttled and not broken:
        print("note: throttling reflects this machine's IP, not the links. "
              "Re-run from a different network if many are throttled.")
    sys.exit(1 if broken else 0)


if __name__ == "__main__":
    main()
