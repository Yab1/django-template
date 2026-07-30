"""
Generated concrete model for Markdown

This model is generated from the abstract Markdown model.
"""

from ehr_common.models import Markdown as AbstractMarkdown


class Markdown(AbstractMarkdown):
    class Meta:
        verbose_name = "Markdown"
        verbose_name_plural = "Markdowns"
        app_label = "fhir"
