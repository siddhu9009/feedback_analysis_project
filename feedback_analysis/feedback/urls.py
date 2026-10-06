from django.urls import path

from feedback.views import (
    submit_form,
    dashboard_view,
    forms_list_view,
    admin_home,
    reports_view,
    report_detail_view,
    download_report,
    export_all_csv,
    export_all_pdf,
    export_form_pdf,
)

urlpatterns = [
    # Modern Admin Dashboard
    path('admin/', admin_home, name='admin_home'),

    # Public form submission
    path('form/<uuid:unique_code>/', submit_form, name='submit_form'),

    # Dashboard per form
    path('dashboard/<int:form_id>/', dashboard_view, name='dashboard_form'),

    # Forms list
    path('forms/', forms_list_view, name='forms_list'),

    # Reports overview
    path('reports/', reports_view, name='reports'),

    # Full report detail for a form
    path('reports/<int:form_id>/', report_detail_view, name='report_detail'),

    # Download CSV report (Single form)
    path('reports/<int:form_id>/download/', download_report, name='download_report'),

    # Download PDF report (Single form)
    path('reports/<int:form_id>/download/pdf/', export_form_pdf, name='export_form_pdf'),

    # Bulk Export (Overall)
    path('export/all/csv/', export_all_csv, name='export_all_csv'),
    path('export/all/pdf/', export_all_pdf, name='export_all_pdf'),
]