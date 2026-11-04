from core.security.registry import register_permission


def register_files_permissions() -> None:
    register_permission(code="files:file:upload", name="Upload a file")
    register_permission(code="files:file:list", name="List files")
    register_permission(code="files:file:list_all", name="List files on any record")
    register_permission(code="files:file:get", name="Get file metadata")
    register_permission(code="files:file:download", name="Download file bytes")
    register_permission(code="files:file:delete", name="Delete a file")
    register_permission(code="files:file:attach_any", name="Attach a file to any record")
