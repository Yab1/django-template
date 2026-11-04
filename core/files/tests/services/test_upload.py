import hashlib

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from core.files.models import FileObject
from core.files.services import file_object_create, file_object_delete
from core.users.models import User


def _user(*, username: str, email: str, phone: int, staff: bool = False) -> User:
    return User.objects.create_user(
        username=username,
        email=email,
        password="NotAWeakPassw0rd!",
        phone_number=phone,
        is_staff=staff,
        is_superuser=staff,
    )


def _pdf(*, name: str = "note.pdf") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, b"%PDF-1.4 test", content_type="application/pdf")


@pytest.mark.django_db
class FileObjectCreateTests:
    def test_upload_maps_user_resource_to_content_type(self):
        user = _user(username="file_owner", email="file_owner@example.com", phone=251911000101)
        row = file_object_create(
            user=user,
            upload=_pdf(),
            resource="user",
            field="file",
            object_id=user.id,
        )
        assert row.resource == "user"
        assert row.field == "file"
        assert row.object_id == user.id
        assert row.content_type.app_label == "users"
        assert row.content_type.model == "user"
        assert row.filename == "note.pdf"
        assert row.media_type == "application/pdf"
        assert row.size > 0
        assert row.file.name
        assert FileObject.objects.filter(pk=row.id).count() == 1

    def test_unknown_resource_rejected(self):
        user = _user(username="file_bad", email="file_bad@example.com", phone=251911000102)
        with pytest.raises(ValidationError):
            file_object_create(
                user=user,
                upload=_pdf(),
                resource="nope",
                field="file",
                object_id=user.id,
            )

    def test_non_staff_cannot_attach_to_other_user(self):
        owner = _user(username="file_a", email="file_a@example.com", phone=251911000103)
        other = _user(username="file_b", email="file_b@example.com", phone=251911000104)
        with pytest.raises(ValidationError):
            file_object_create(
                user=owner,
                upload=_pdf(),
                resource="user",
                field="file",
                object_id=other.id,
            )

    def test_staff_can_attach_to_other_user(self):
        staff = _user(username="file_staff", email="file_staff@example.com", phone=251911000105, staff=True)
        other = _user(username="file_target", email="file_target@example.com", phone=251911000106)
        row = file_object_create(
            user=staff,
            upload=_pdf(),
            resource="user",
            field="file",
            object_id=other.id,
        )
        assert row.object_id == other.id
        assert row.created_by_id == staff.id

    def test_disallowed_media_type(self, settings):
        settings.FILE_ALLOWED_TYPES = ["application/pdf"]
        user = _user(username="file_mime", email="file_mime@example.com", phone=251911000107)
        upload = SimpleUploadedFile("note.txt", b"hello", content_type="text/plain")
        with pytest.raises(ValidationError):
            file_object_create(
                user=user,
                upload=upload,
                resource="user",
                field="file",
                object_id=user.id,
            )

    def test_delete_soft_hides_row(self):
        user = _user(username="file_del", email="file_del@example.com", phone=251911000108)
        row = file_object_create(
            user=user,
            upload=_pdf(),
            resource="user",
            field="file",
            object_id=user.id,
        )
        file_object_delete(file_id=row.id, user=user)
        row.refresh_from_db()
        assert row.deleted_at is not None

    def test_serializer_returns_storage_url_not_key(self):
        from core.files.serializers import FileObjectSerializer

        user = _user(username="file_url", email="file_url@example.com", phone=251911000109)
        row = file_object_create(
            user=user,
            upload=_pdf(),
            resource="user",
            field="file",
            object_id=user.id,
        )
        data = FileObjectSerializer(row).data
        assert "key" not in data
        assert data["url"] == row.file.url


class _FakeClamd:
    def __init__(self, reply: bytes):
        self.reply = reply

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> bool:
        return False

    def sendall(self, data: bytes) -> None:
        pass

    def recv(self, size: int) -> bytes:
        reply, self.reply = self.reply, b""
        return reply


def _clamd(monkeypatch, *, reply: bytes | None) -> None:
    def connect(*args, **kwargs):
        if reply is None:
            raise ConnectionRefusedError
        return _FakeClamd(reply)

    monkeypatch.setattr("core.files.adapters.clamav.socket.create_connection", connect)


def _upload_own_file(*, user: User) -> FileObject:
    return file_object_create(user=user, upload=_pdf(), resource="user", field="file", object_id=user.id)


@pytest.mark.django_db
class FileObjectScanTests:
    def test_clean_upload_is_saved_with_hash(self, settings, monkeypatch):
        settings.CLAMAV_ENABLED = True
        _clamd(monkeypatch, reply=b"stream: OK\0")
        user = _user(username="scan_ok", email="scan_ok@example.com", phone=251911000110)
        row = _upload_own_file(user=user)
        assert row.content_hash == hashlib.sha256(b"%PDF-1.4 test").hexdigest()

    def test_infected_upload_is_rejected(self, settings, monkeypatch):
        settings.CLAMAV_ENABLED = True
        _clamd(monkeypatch, reply=b"stream: Eicar-Test-Signature FOUND\0")
        user = _user(username="scan_bad", email="scan_bad@example.com", phone=251911000111)
        with pytest.raises(ValidationError):
            _upload_own_file(user=user)
        assert not FileObject.objects.filter(object_id=user.id).exists()

    def test_upload_is_rejected_when_clamd_is_down(self, settings, monkeypatch):
        settings.CLAMAV_ENABLED = True
        _clamd(monkeypatch, reply=None)
        user = _user(username="scan_down", email="scan_down@example.com", phone=251911000112)
        with pytest.raises(ValidationError):
            _upload_own_file(user=user)

    def test_scan_is_skipped_when_disabled(self, settings, monkeypatch):
        settings.CLAMAV_ENABLED = False
        _clamd(monkeypatch, reply=None)
        user = _user(username="scan_off", email="scan_off@example.com", phone=251911000113)
        row = _upload_own_file(user=user)
        assert row.content_hash
