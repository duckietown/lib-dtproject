import socket
from typing import Optional

from dockertown import DockerClient

DEFAULT_DOCKER_TCP_PORT = "2375"


def docker_client(endpoint) -> DockerClient:
    return (
        endpoint
        if isinstance(endpoint, DockerClient)
        else DockerClient(host=sanitize_docker_baseurl(endpoint))
    )


def sanitize_docker_baseurl(baseurl: str, port=DEFAULT_DOCKER_TCP_PORT) -> Optional[str]:
    if baseurl is None:
        return None
    if baseurl.startswith("unix:"):
        return baseurl
    elif baseurl.startswith("tcp://"):
        return resolve_hostname(baseurl)
    else:
        url = resolve_hostname(baseurl)
        if not url.startswith("tcp://"):
            url = f"tcp://{url}"
        if url.count(":") == 1:
            url = f"{url}:{port}"
        return url


def resolve_hostname(hostname: str) -> str:
    # separate protocol (if any)
    protocol = ""
    if "://" in hostname:
        idx = hostname.index("://")
        protocol, hostname = hostname[0: idx + len("://")], hostname[idx + len("://"):]
    # separate port (if any)
    port = ""
    if ":" in hostname:
        idx = hostname.index(":")
        hostname, port = hostname[0:idx], hostname[idx:]
    # perform name resolution
    ip = socket.gethostbyname(hostname)
    return protocol + ip + port
