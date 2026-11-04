from core.files.apis.delete import FileDeleteApi
from core.files.apis.get import FileDownloadApi, FileGetApi
from core.files.apis.list import FileListApi
from core.files.apis.upload import FileUploadApi


class FileDetailApi(FileGetApi, FileDeleteApi):
    """GET and DELETE share `/files/<uuid>/`. Method is the action."""

    authorization_actions = {
        "GET": "files:file:get",
        "DELETE": "files:file:delete",
    }


__all__ = [
    "FileDeleteApi",
    "FileDetailApi",
    "FileDownloadApi",
    "FileGetApi",
    "FileListApi",
    "FileUploadApi",
]
