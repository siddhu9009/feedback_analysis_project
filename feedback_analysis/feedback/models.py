from django.db import models
from django.conf import settings
import uuid


class Form(models.Model):
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    unique_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def get_public_link(self):
        base_url = getattr(settings, "NGROK_BASE_URL", "")
        if base_url:
            return f"{base_url}/form/{self.unique_code}/"
        return "Set NGROK_BASE_URL in settings"

    def __str__(self):
        return self.title


class FormField(models.Model):
    TEXT     = 'text'
    NUMBER   = 'number'
    DROPDOWN = 'dropdown'

    FIELD_TYPES = [
        (TEXT,     'Text'),
        (NUMBER,   'Number'),
        (DROPDOWN, 'Dropdown'),
    ]

    form            = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='fields')
    label           = models.CharField(max_length=200)
    field_type      = models.CharField(max_length=20, choices=FIELD_TYPES)
    choices         = models.TextField(blank=True, help_text="Comma-separated options for dropdown")
    required        = models.BooleanField(default=True)

    # ── If False, skip avg/min/max (use for phone, vehicle number etc.) ───────
    calculate_stats = models.BooleanField(
        default=True,
        help_text="Uncheck for phone numbers, vehicle numbers — skips average/min/max calculation"
    )

    def __str__(self):
        return f"{self.label} ({self.field_type})"


class Response(models.Model):
    form         = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='responses')
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response {self.id} - {self.form.title}"


class ResponseAnswer(models.Model):
    POSITIVE = 'positive'
    NEUTRAL  = 'neutral'
    NEGATIVE = 'negative'

    SENTIMENT_CHOICES = [
        (POSITIVE, 'Positive'),
        (NEUTRAL,  'Neutral'),
        (NEGATIVE, 'Negative'),
    ]

    response    = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='answers')
    field       = models.ForeignKey(FormField, on_delete=models.CASCADE)
    answer_text = models.TextField()
    sentiment   = models.CharField(
        max_length=10,
        choices=SENTIMENT_CHOICES,
        blank=True,
        null=True,
    )

    # ── AI Analysis & Insights ────────────────────────────────────────────────
    ai_issues         = models.TextField(blank=True, null=True, help_text="Detected product/service issues")
    ai_suggestions    = models.TextField(blank=True, null=True, help_text="Suggested product/service improvements")
    form_issues       = models.TextField(blank=True, null=True, help_text="Detected issues with the form itself")
    form_improvements = models.TextField(blank=True, null=True, help_text="Suggested improvements for form quality")

    def __str__(self):
        return f"{self.field.label}: {self.answer_text}"