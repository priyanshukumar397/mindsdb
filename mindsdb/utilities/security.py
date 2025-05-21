from urllib.parse import urlparse
import socket
import ipaddress


def is_private_url(url: str):
    """
    Raises exception if url is private

    :param url: url to check
    """

    hostname = urlparse(url).hostname
    if not hostname:
        # Unable find hostname in url
        return True
    ip = socket.gethostbyname(hostname)
    return ipaddress.ip_address(ip).is_private


def clear_filename(filename: str) -> str:
    """
    Removes path symbols from filename which could be used for path injection
    :param filename: input filename
    :return: output filename
    """

    if not filename:
        # If original filename is empty or None, return a default name.
        return "default_filename"

    from pathlib import Path

    # Extract the basename using Path().name. This handles '/', '\', '../' etc.
    cleaned_filename = Path(filename).name

    # If Path().name results in an empty string (e.g., from input like "/", ".", "..", or "foo/"),
    # provide a default name.
    if not cleaned_filename:
        cleaned_filename = "default_filename"

    # Sanitize additional problematic characters that might be valid in some OS paths
    # but are generally unwanted or could cause issues in web contexts or specific filesystems.
    # Path().name would have already handled '/' and '\' by giving the basename.
    badchars = ':*?\"<>|'
    for char in badchars:
        cleaned_filename = cleaned_filename.replace(char, '_') # Replace with underscore

    # If after replacements, the filename consists only of underscores or is empty,
    # (e.g., original was "::" or "///" which Path().name makes "" then default_filename,
    # or original was "_:_<_")
    # return a default name.
    if not cleaned_filename.strip('_'):
        cleaned_filename = "default_filename"
        
    return cleaned_filename


def validate_urls(urls, allowed_urls):
    """
    Checks if the provided URL(s) is/are from an allowed host.

    This function parses the URL(s) and checks the network location part (netloc)
    against a list of allowed hosts.

    :param urls: The URL(s) to check. Can be a single URL (str) or a list of URLs (list).
    :param allowed_urls: The list of allowed URLs.
    :return bool:  True if the URL(s) is/are from an allowed host, False otherwise.
    """
    allowed_netlocs = [urlparse(allowed_url).netloc for allowed_url in allowed_urls]

    if isinstance(urls, str):
        urls = [urls]

    # Check if all provided URLs are from the allowed sites
    valid = all(urlparse(url).netloc in allowed_netlocs for url in urls)
    return valid
