"""
Generated concrete model for Annotation

This model is generated from the abstract Annotation model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import Annotation as AbstractAnnotation


class Annotation(AbstractAnnotation):
    author = models.ForeignKey(
        "fhir.Author",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="annotation_author",
        help_text=_("Individual responsible for the annotation."),
    )

    class Meta:
        verbose_name = "Annotation"
        verbose_name_plural = "Annotations"
        app_label = "fhir"
