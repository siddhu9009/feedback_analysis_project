from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import render, get_object_or_404
from django.utils.html import format_html
from django import forms

from .models import Form, FormField, Response, ResponseAnswer


# ─────────────────────────────────────────────
# 🔥 FIX: Prevent label duplication in admin
# ─────────────────────────────────────────────
class FormFieldAdminForm(forms.ModelForm):
    class Meta:
        model = FormField
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Prevent Django adding extra label suffix / duplication issues
        for field in self.fields.values():
            field.label_suffix = ""


# ── Inline for Form Fields ────────────────────────────────────────────────
class FormFieldInline(admin.TabularInline):
    model = FormField
    form = FormFieldAdminForm   # 🔥 IMPORTANT FIX
    extra = 1

    fields = [
        'label',
        'field_type',
        'choices',
        'required',
        'calculate_stats'
    ]

    verbose_name_plural = "Form Fields (💡 Stats ON: Age/Score | OFF: Phone/Vehicle No.)"


# ── Form Admin ────────────────────────────────────────────────────────────
class FormAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'share_qr', 'copy_link', 'view_submissions')
    inlines = [FormFieldInline]

    search_fields = ('title', 'description')

    def public_link(self, obj):
        link = obj.get_public_link()
        return format_html(
            '<input type="text" value="{}" readonly '
            'style="width:250px;padding:6px;border:1px solid var(--border);'
            'border-radius:6px;background:var(--bg);color:var(--text);font-size:0.75rem;">',
            link
        )
    public_link.short_description = "URL"

    def share_qr(self, obj):
        link = obj.get_public_link()
        title_escaped = obj.title.replace("'", "\\'")

        return format_html(
            '<button type="button" class="action-btn" '
            'onclick="openShareModal(\'{}\', \'{}\')">'
            '<i class="bi bi-qr-code"></i> Share</button>',
            title_escaped,
            link
        )
    share_qr.short_description = "Share"

    def copy_link(self, obj):
        link = obj.get_public_link()

        return format_html(
            '<button type="button" class="action-btn" '
            'onclick="navigator.clipboard.writeText(\'{}\'); '
            'this.innerHTML=\'<i class=\\\'bi bi-check-lg\\\'></i> Copied\'; '
            'setTimeout(()=>this.innerHTML=\'<i class=\\\'bi bi-link-45deg\\\'></i> Copy Link\', 2000);">'
            '<i class="bi bi-link-45deg"></i> Copy Link</button>',
            link
        )
    copy_link.short_description = "Link"

    def view_submissions(self, obj):
        url = reverse('admin:form-submissions', args=[obj.id])
        return format_html(
            '<a href="{}" class="action-btn" style="color:var(--primary);">'
            '<i class="bi bi-bar-chart-fill"></i> Data</a>',
            url
        )
    view_submissions.short_description = "Stats"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:form_id>/submissions/',
                self.admin_site.admin_view(self.submissions_view),
                name='form-submissions'
            ),
        ]
        return custom_urls + urls

    def submissions_view(self, request, form_id):
        form = get_object_or_404(Form, id=form_id)
        fields = form.fields.all()
        responses = Response.objects.filter(form=form)

        table_data = []

        for response in responses:
            answers = []

            for field in fields:
                answer_obj = ResponseAnswer.objects.filter(
                    response=response,
                    field=field
                ).first()

                answers.append(answer_obj.answer_text if answer_obj else "")

            table_data.append({
                "submitted_at": response.submitted_at,
                "answers": answers,
            })

        return render(request, "admin/form_submissions.html", {
            "form": form,
            "fields": fields,
            "table_data": table_data,
            "dashboard_link": reverse('admin:index'),
        })


# ── FormField Admin ───────────────────────────────────────────────────────
@admin.register(FormField)
class FormFieldAdmin(admin.ModelAdmin):
    list_display = ['label', 'form', 'field_type', 'required', 'calculate_stats']
    list_editable = ['calculate_stats']
    list_filter = ['field_type', 'form', 'calculate_stats']
    search_fields = ['label']


# ── ResponseAnswer Admin ──────────────────────────────────────────────────
@admin.register(ResponseAnswer)
class ResponseAnswerAdmin(admin.ModelAdmin):
    list_display = [
        'field',
        'answer_text',
        'sentiment',
        'ai_issues',
        'form_issues'
    ]
    list_filter = ['sentiment', 'ai_issues']
    search_fields = [
        'answer_text',
        'ai_issues',
        'ai_suggestions',
        'form_issues',
        'form_improvements'
    ]


# ── Response Answer Inline ────────────────────────────────────────────────
class ResponseAnswerInline(admin.TabularInline):
    model = ResponseAnswer
    extra = 0
    fields = ('field', 'answer_text', 'sentiment', 'ai_issues')
    readonly_fields = ('field',)


# ── Response Admin ────────────────────────────────────────────────────────
@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('id', 'form', 'submitted_at')
    list_filter = ('form',)
    search_fields = ('form__title',)
    inlines = [ResponseAnswerInline]


# ── Register Form ─────────────────────────────────────────────────────────
admin.site.register(Form, FormAdmin)


# ── Admin Branding ────────────────────────────────────────────────────────
admin.site.site_header = format_html(
    'Admin Panel &nbsp; <a href="{}" style="color:#a5b4fc;font-weight:700;">'
    '→ FeedbackIQ Dashboard</a>',
    '/admin/'
)

admin.site.index_title = "Admin Panel"
admin.site.site_title = "FeedbackIQ"