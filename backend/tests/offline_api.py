"""Test server: deny Python internet sockets while preserving loopback."""

import errno
import ipaddress
import socket

import uvicorn

from app.main import create_app

denials = 0
connect = socket.socket.connect
connect_ex = socket.socket.connect_ex


def allowed(address):
    if not isinstance(address, tuple):
        return True
    try:
        return ipaddress.ip_address(address[0]).is_loopback
    except ValueError:
        return False


def guarded_connect(self, address):
    global denials
    if not allowed(address):
        denials += 1
        raise PermissionError("Internet disabled by local verification guard.")
    return connect(self, address)


def guarded_connect_ex(self, address):
    global denials
    if not allowed(address):
        denials += 1
        return errno.EPERM
    return connect_ex(self, address)


if __name__ == "__main__":
    socket.socket.connect = guarded_connect
    socket.socket.connect_ex = guarded_connect_ex
    with socket.socket() as probe:
        try:
            probe.connect(("198.51.100.1", 443))
        except PermissionError:
            pass
        else:
            raise RuntimeError("Internet guard failed.")
    probe_denials = denials
    application = create_app()

    @application.get("/test/network-policy")
    def policy():
        return dict(
            internet_denied=True,
            blocked_probe=probe_denials,
            runtime_denials=denials - probe_denials,
        )

    @application.post("/test/unexpected")
    def unexpected():
        raise RuntimeError("dummyprivacy@example.invalid")

    uvicorn.run(application, host="127.0.0.1", port=8000, access_log=False, proxy_headers=False)
