"""MinIO media storage that asks the server to encrypt objects with SSE-S3."""

import minio.error as merr
from minio.sse import SseS3
from minio_storage.errors import minio_error
from minio_storage.storage import MinioMediaStorage


class SseMinioMediaStorage(MinioMediaStorage):
    def _save(self, name: str, content) -> str:
        try:
            if hasattr(content, "seek") and callable(content.seek):
                content.seek(0)
            content_size, content_type, sane_name = self._examine_file(name, content)
            self.client.put_object(
                self.bucket_name,
                sane_name,
                content,
                content_size,
                content_type,
                metadata=self.object_metadata,  # type: ignore[arg-type]
                sse=SseS3(),
            )
            return sane_name
        except merr.InvalidResponseError as error:
            raise minio_error(f"File {name} could not be saved", error) from error
