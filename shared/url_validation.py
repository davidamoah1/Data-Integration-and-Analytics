"""URL validation utilities to prevent SSRF attacks.

Validates that user-supplied URLs:
- Use allowed protocols (http, https only)
- Do not target internal/private network ranges
- Do not target localhost or link-local addresses
"""

import ipaddress
import socket
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"http", "https"}
BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),       # IPv4 loopback
    ipaddress.ip_network("10.0.0.0/8"),        # Private
    ipaddress.ip_network("172.16.0.0/12"),     # Private
    ipaddress.ip_network("192.168.0.0/16"),    # Private
    ipaddress.ip_network("169.254.0.0/16"),    # Link-local
    ipaddress.ip_network("0.0.0.0/8"),         # Current network
    ipaddress.ip_network("::1/128"),           # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),          # IPv6 ULA
    ipaddress.ip_network("fe80::/10"),         # IPv6 link-local
]


class UrlValidationError(ValueError):
    """Raised when a URL fails SSRF validation."""


def validate_url(url: str, *, allow_localhost: bool = False) -> str:
    """Validate a URL to prevent SSRF attacks.

    Args:
        url: The URL to validate.
        allow_localhost: If True, allow localhost/127.0.0.1 (for dev only).

    Returns:
        The validated URL string.

    Raises:
        UrlValidationError: If the URL is invalid or targets a blocked host.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise UrlValidationError(
            f"URL scheme '{parsed.scheme}' is not allowed. Only http and https are permitted."
        )
    if not parsed.hostname:
        raise UrlValidationError("URL must include a hostname.")

    hostname = parsed.hostname

    # Block obvious localhost strings
    if not allow_localhost:
        if hostname.lower() in ("localhost", "0.0.0.0", "::"):
            raise UrlValidationError("Requests to localhost are not allowed.")

    # Resolve hostname and check against blocked networks
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise UrlValidationError(f"Could not resolve hostname: {hostname}") from None

    for info in infos:
        ip = info[4][0]
        try:
            ip_obj = ipaddress.ip_address(ip)
        except ValueError:
            continue

        if not allow_localhost:
            for network in BLOCKED_NETWORKS:
                if ip_obj in network:
                    raise UrlValidationError(
                        f"URL hostname '{hostname}' resolves to a blocked "
                        f"network address: {ip_obj}."
                    )

    return url
