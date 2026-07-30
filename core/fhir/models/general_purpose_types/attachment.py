"""
Generated concrete model for Attachment

This model is generated from the abstract Attachment model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import Attachment as AbstractAttachment


class Attachment(AbstractAttachment):
    content_type = models.ForeignKey(
        "fhir.Coding",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attachment_content_type",
        help_text=_("Mime type of the content, with charset etc. (e.g., 'text/plain; charset=UTF-8')"),
    )

    language = models.ForeignKey(
        "fhir.Coding",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attachment_language",
        help_text=_("Human language of the content (BCP-47). Used for text-based attachments."),
    )

    class Meta:
        verbose_name = "Attachment"
        verbose_name_plural = "Attachments"
        app_label = "fhir"
