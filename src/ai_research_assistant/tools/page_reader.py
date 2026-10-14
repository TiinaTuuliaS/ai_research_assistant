"""Bounded public-page retrieval. Never follow redirects into private networks."""
import ipaddress
import socket
import time
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup
import urllib3
from ..source_registry import iso_date

MAX_BYTES = 500_000
MAX_TEXT = 8000


def public_target(url):
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("unsupported URL")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if port not in {80, 443}:
        raise ValueError("unsupported port")
    host = parsed.hostname.encode("idna").decode("ascii")
    addresses = [entry[4][0] for entry in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)]
    if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):
        raise ValueError("non-public address")
    return parsed, host, port, addresses[0]


def read_page(url):
    """Return evidence metadata, including explicit failures, never fabricated text."""
    current = url
    deadline = time.monotonic() + 12
    try:
        for _ in range(3):
            parsed, host, port, address = public_target(current)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError()
            # Connect to the validated IP, preserving TLS hostname verification.
            # This prevents a second DNS lookup from redirecting into a LAN.
            pool_class = urllib3.HTTPSConnectionPool if parsed.scheme == "https" else urllib3.HTTPConnectionPool
            tls = {"server_hostname": host, "assert_hostname": host, "cert_reqs": "CERT_REQUIRED"} if parsed.scheme == "https" else {}
            with pool_class(address, port, **tls) as pool:
                path = parsed.path or "/"
                if parsed.query:
                    path += "?" + parsed.query
                response = pool.urlopen("GET", path, headers={"Host": host, "User-Agent": "ResearchAssistant/1.0",
                    "Accept": "text/html,text/plain", "Accept-Encoding": "identity"},
                    redirect=False, retries=False, preload_content=False,
                    timeout=urllib3.Timeout(connect=min(4, remaining), read=min(4, remaining), total=remaining))
                try:
                    if response.status in {301, 302, 303, 307, 308}:
                        current = urljoin(current, response.headers.get("Location", ""))
                        continue
                    if response.status != 200:
                        return {"page_status": "unavailable", "page_reason": "http_error"}
                    content_type = response.headers.get("Content-Type", "").lower()
                    if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                        return {"page_status": "unavailable", "page_reason": "unsupported_encoding"}
                    if not any(kind in content_type for kind in ("text/html", "application/xhtml+xml", "text/plain")):
                        return {"page_status": "unavailable", "page_reason": "unsupported_content"}
                    chunks, size = [], 0
                    while size <= MAX_BYTES:
                        if time.monotonic() > deadline:
                            raise TimeoutError()
                        chunk = response.read(min(16384, MAX_BYTES + 1 - size), decode_content=False)
                        if not chunk:
                            break
                        chunks.append(chunk)
                        size += len(chunk)
                    if size > MAX_BYTES:
                        return {"page_status": "unavailable", "page_reason": "page_too_large"}
                    parsed_html = BeautifulSoup(b"".join(chunks), "html.parser")
                    publication = parsed_html.find('meta', attrs={'property': 'article:published_time'})
                    if publication is None:
                        publication = parsed_html.find('meta', attrs={'itemprop': 'datePublished'})
                    published_at = iso_date(publication.get('content')) if publication else None
                    for tag in parsed_html(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
                        tag.decompose()
                    content = parsed_html.find('article') or parsed_html.find('main') or parsed_html
                    text = " ".join(content.get_text(" ", strip=True).split())
                    if len(text) < 100:
                        return {"page_status": "unavailable", "page_reason": "insufficient_text"}
                    return {"page_status": "retrieved", "page_text": text[:MAX_TEXT],
                            "page_truncated": len(text) > MAX_TEXT, "page_url": current,
                            **({'published_at': published_at, 'publication_date_basis': 'article_metadata'} if published_at else {})}
                finally:
                    response.close()
        return {"page_status": "unavailable", "page_reason": "redirect_limit"}
    except (ValueError, OSError, urllib3.exceptions.HTTPError, TimeoutError):
        return {"page_status": "unavailable", "page_reason": "blocked_or_unreachable"}
