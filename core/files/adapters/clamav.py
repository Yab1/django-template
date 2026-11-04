import socket

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile


def clamav_scan(*, upload: UploadedFile) -> None:
    """Stream the upload to clamd with INSTREAM. Raise unless clamd answers OK."""
    try:
        with socket.create_connection(
            (settings.CLAMAV_HOST, settings.CLAMAV_PORT),
            timeout=settings.CLAMAV_TIMEOUT,
        ) as sock:
            sock.sendall(b"zINSTREAM\0")
            for chunk in upload.chunks():
                sock.sendall(len(chunk).to_bytes(4, "big") + chunk)
            sock.sendall(b"\0\0\0\0")
            reply = b""
            while not reply.endswith(b"\0"):
                part = sock.recv(4096)
                if not part:
                    break
                reply += part
    except OSError as exc:
        raise ValidationError({"file": "Virus scan is unavailable. Try again later."}) from exc

    answer = reply.rstrip(b"\0").decode("utf-8", errors="replace")
    if answer.endswith("FOUND"):
        raise ValidationError({"file": "File failed virus scan."})
    if not answer.endswith("OK"):
        raise ValidationError({"file": "Virus scan is unavailable. Try again later."})
