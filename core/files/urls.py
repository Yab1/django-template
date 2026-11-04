from django.urls import path

from core.files.apis import FileDetailApi, FileDownloadApi, FileListApi, FileUploadApi

app_name = "files"

urlpatterns = [
    path("files/", FileListApi.as_view(), name="file-list"),
    path("files/upload/", FileUploadApi.as_view(), name="file-upload"),
    path("files/<uuid:file_id>/download/", FileDownloadApi.as_view(), name="file-download"),
    path("files/<uuid:file_id>/", FileDetailApi.as_view(), name="file-detail"),
]
