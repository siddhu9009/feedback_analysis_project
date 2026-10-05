from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.db.models import Count, Avg, FloatField
from django.db.models.functions import Cast, TruncDate
from .models import Form, FormField, Response, ResponseAnswer
from .sentiment_utils import analyze_sentiment, get_sentiment_summary, analyze_feedback_insights
import json
import csv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


from django.contrib.auth.decorators import login_required


# ============================
# Admin Home
# ============================
@login_required(login_url='/admin_django/login/')
def admin_home(request):
    total_forms      = Form.objects.count()
    total_responses  = Response.objects.count()
    all_text_answers = ResponseAnswer.objects.filter(field__field_type='text')
    overall_sentiment = get_sentiment_summary(all_text_answers)
    # ── RECENT ACTIVITY ──
    recent_forms = Form.objects.all().order_by('-created_at')[:5]
    recent_responses = Response.objects.all().select_related('form').order_by('-submitted_at')[:5]
    
    activities = []
    for f in recent_forms:
        activities.append({
            'title': 'New form created',
            'desc': f'"{f.title}" was published.',
            'time': f.created_at,
            'icon': 'bi-file-earmark-plus',
            'color': 'blue'
        })
    for r in recent_responses:
        activities.append({
            'title': 'New response received',
            'desc': f'A response was submitted for "{r.form.title}".',
            'time': r.submitted_at,
            'icon': 'bi-reply-all',
            'color': 'green'
        })
        
    activities.sort(key=lambda x: x['time'], reverse=True)
    recent_activities = activities[:3]
    
    # ── RESPONSE TREND ──
    response_trend_qs   = (Response.objects.all()
                           .annotate(day=TruncDate('submitted_at'))
                           .values('day')
                           .annotate(count=Count('id'))
                           .order_by('day'))
    response_trend_json = json.dumps(list(response_trend_qs), default=str)

    context = {
        'total_forms':        total_forms,
        'total_responses':    total_responses,
        'overall_sentiment':  overall_sentiment,
        'recent_activities':  recent_activities,
        'response_trend':     response_trend_json,
    }
    return render(request, 'feedback/admin_home.html', context)


# ============================
# Forms List
# ============================
@login_required(login_url='/admin_django/login/')
def forms_list_view(request):
    q = request.GET.get('q', '')

    if q:
        forms = Form.objects.filter(title__icontains=q).order_by('-id')
    else:
        forms = Form.objects.all().order_by('-id')

    # AI SUMMARY PER FORM (BASED ON RESPONSES)
    for form in forms:
        text_answers = ResponseAnswer.objects.filter(
            field__field_type='text',
            response__form=form
        )

        if text_answers.exists():
            responses_list = [
                f"- {a.answer_text.strip()}"
                for a in text_answers if a.answer_text.strip()
            ]

            combined_text = "\n".join(responses_list[:50])  # limit for performance

            try:
                analysis = analyze_feedback_insights(combined_text)

                form.ai_summary = {
                    'issues': analysis.get('ai_issues', ''),
                    'positives': analysis.get('positives', ''),
                    'suggestions': analysis.get('ai_suggestions', ''),
                }

            except Exception:
                form.ai_summary = None
        else:
            form.ai_summary = None

    return render(request, 'feedback/forms_list.html', {
        'forms': forms,
        'q': q
    })


# ============================
# Public Form Submission
# ============================
def submit_form(request, unique_code):
    form   = get_object_or_404(Form, unique_code=unique_code)
    fields = form.fields.all()

    for field in fields:
        if field.field_type == 'dropdown' and field.choices:
            field.choices_list = [c.strip() for c in field.choices.split(',')]

    if request.method == 'POST':
        response = Response.objects.create(form=form)

        for field in fields:
            value = request.POST.get(f'field_{field.id}', '')

            sentiment = None
            ai_issues = ''
            ai_suggestions = ''
            
            if field.field_type == 'text' and value.strip():
                analysis = analyze_feedback_insights(value)
                sentiment = analysis.get('sentiment')
                ai_issues = analysis.get('ai_issues', '')
                ai_suggestions = analysis.get('ai_suggestions', '')

            ResponseAnswer.objects.create(
                response=response,
                field=field,
                answer_text=value,
                sentiment=sentiment,
                ai_issues=ai_issues,
                ai_suggestions=ai_suggestions
            )

        return render(request, 'feedback/thank_you.html', {'form': form})

    return render(request, 'feedback/form.html', {'form': form, 'fields': fields})


# ============================
# Helper: build field data dict
# ============================
def _build_field_data(field, answers):
    field_data = {
        'label': field.label,
        'type': field.field_type,
        'total_answers': answers.count(),
        'calculate_stats': field.calculate_stats,
    }

    if field.field_type == 'number':
        if field.calculate_stats:
            numeric_data = answers.annotate(numeric_value=Cast('answer_text', FloatField()))
            avg_value = numeric_data.aggregate(avg=Avg('numeric_value'))['avg']
            min_obj = numeric_data.order_by('numeric_value').first()
            max_obj = numeric_data.order_by('-numeric_value').first()

            field_data.update({
                'average': round(avg_value, 2) if avg_value else 0,
                'min': float(min_obj.answer_text) if min_obj else 0,
                'max': float(max_obj.answer_text) if max_obj else 0,
            })
        else:
            # ✅ FIX: only last 4
            recent = answers.order_by('-id')[:4]
            field_data['recent_answers'] = [a.answer_text for a in recent]

    elif field.field_type == 'dropdown':
        stats = answers.values('answer_text').annotate(total=Count('id')).order_by('-total')
        field_data['distribution'] = json.dumps(list(stats))

    elif field.field_type == 'text':
        # ✅ FIX: only last 4
        recent = answers.order_by('-id')[:4]

        field_data['recent_answers'] = [
            {'text': a.answer_text, 'sentiment': a.sentiment or 'neutral'}
            for a in recent
        ]

        field_data['sentiment'] = get_sentiment_summary(answers)

    return field_data


# ============================
# Form Analytics Dashboard
# ============================
@login_required(login_url='/admin_django/login/')
def dashboard_view(request, form_id):
    form            = get_object_or_404(Form, id=form_id)
    responses       = Response.objects.filter(form=form)
    fields          = FormField.objects.filter(form=form)
    total_responses = responses.count()

    response_trend_qs   = (responses
                           .annotate(day=TruncDate('submitted_at'))
                           .values('day')
                           .annotate(count=Count('id'))
                           .order_by('day'))
    response_trend_json = json.dumps(list(response_trend_qs), default=str)

    text_answers      = ResponseAnswer.objects.filter(field__field_type='text', response__in=responses)
    sentiment_summary = get_sentiment_summary(text_answers)

    # ✅ AI SUMMARY
    ai_summary = None
    if text_answers.exists():
        responses_list = [
            f"- {a.answer_text.strip()}"
            for a in text_answers if a.answer_text.strip()
        ]
        combined_text = "\n".join(responses_list[:50])
        try:
            analysis = analyze_feedback_insights(combined_text)
            ai_summary = {
                'issues': analysis.get('ai_issues', ''),
                'positives': analysis.get('positives', ''),
                'suggestions': analysis.get('ai_suggestions', ''),
            }
        except Exception:
            pass

    sentiment_trend_qs   = (text_answers
                            .annotate(day=TruncDate('response__submitted_at'))
                            .values('day', 'sentiment')
                            .annotate(count=Count('id'))
                            .order_by('day'))
    sentiment_trend_json = json.dumps(list(sentiment_trend_qs), default=str)

    field_analytics = []
    for field in fields:
        answers = ResponseAnswer.objects.filter(field=field, response__in=responses)
        field_analytics.append(_build_field_data(field, answers))

    context = {
        'form':              form,
        'total_responses':   total_responses,
        'field_analytics':   field_analytics,
        'response_trend':    response_trend_json,
        'sentiment_summary': sentiment_summary,
        'sentiment_trend':   sentiment_trend_json,
        'ai_summary':        ai_summary,
    }
    return render(request, 'feedback/dashboard.html', context)

    
    
# ============================
# Reports Overview
# ============================
@login_required(login_url='/admin_django/login/')
def reports_view(request):
    forms       = Form.objects.all().order_by('-created_at')
    report_data = []

    for form in forms:
        responses         = Response.objects.filter(form=form)
        total_responses   = responses.count()
        text_answers      = ResponseAnswer.objects.filter(field__field_type='text', response__in=responses)
        sentiment_summary = get_sentiment_summary(text_answers)
        
        field_stats = []
        for field in form.fields.all():
            answers = ResponseAnswer.objects.filter(field=field, response__in=responses)
            data    = _build_field_data(field, answers)
            # For reports page, distribution should be a list not JSON string
            if field.field_type == 'dropdown' and 'distribution' in data:
                data['distribution'] = json.loads(data['distribution'])
            field_stats.append(data)

        report_data.append({
            'form':              form,
            'total_responses':   total_responses,
            'sentiment_summary': sentiment_summary,
            'fields':            field_stats,
        })

    return render(request, 'feedback/reports.html', {'report_data': report_data})


# ============================
# Report Detail
# ============================
@login_required(login_url='/admin_django/login/')
def report_detail_view(request, form_id):
    form      = get_object_or_404(Form, id=form_id)
    responses = Response.objects.filter(form=form).prefetch_related('answers__field')
    fields    = list(form.fields.all())
    total_responses = responses.count()

    text_answers      = ResponseAnswer.objects.filter(field__field_type='text', response__in=responses)
    sentiment_summary = get_sentiment_summary(text_answers)

    all_responses_data = []
    for resp in responses:
        answers = {a.field.label: {'text': a.answer_text, 'sentiment': a.sentiment or ''}
                   for a in resp.answers.all()}
        all_responses_data.append({
            'id':           resp.id,
            'submitted_at': resp.submitted_at,
            'answers':      answers,
        })

    return render(request, 'feedback/report_detail.html', {
        'form': form,
        'fields': fields,
        'total_responses': total_responses,
        'sentiment_summary': sentiment_summary,
        'all_responses': all_responses_data,
    })


# ============================
# Download CSV
# ============================
@login_required(login_url='/admin_django/login/')
def download_report(request, form_id):
    form      = get_object_or_404(Form, id=form_id)
    responses = Response.objects.filter(form=form).prefetch_related('answers__field')
    fields    = list(form.fields.all())

    response_http = HttpResponse(content_type='text/csv')
    response_http['Content-Disposition'] = f'attachment; filename="{form.title}_report.csv"'

    writer = csv.writer(response_http)
    header = ['Response ID', 'Submitted At'] + [f.label for f in fields]
    writer.writerow(header)

    for resp in responses:
        answer_map = {a.field_id: a for a in resp.answers.all()}
        row        = [resp.id, resp.submitted_at.strftime('%Y-%m-%d %H:%M')]

        for field in fields:
            ans = answer_map.get(field.id)
            row.append(ans.answer_text if ans else '')

        writer.writerow(row)

    return response_http


# ============================
# Export ALL CSV
# ============================
@login_required(login_url='/admin_django/login/')
def export_all_csv(request):
    responses = Response.objects.all().select_related('form').prefetch_related('answers__field').order_by('-submitted_at')
    
    response_http = HttpResponse(content_type='text/csv')
    response_http['Content-Disposition'] = 'attachment; filename="all_forms_feedback.csv"'

    writer = csv.writer(response_http)
    writer.writerow(['Form Title', 'Response ID', 'Date', 'Field Label', 'Answer Text', 'Sentiment'])

    for resp in responses:
        for ans in resp.answers.all():
            writer.writerow([
                resp.form.title,
                resp.id,
                resp.submitted_at.strftime('%Y-%m-%d %H:%M'),
                ans.field.label,
                ans.answer_text,
                ans.sentiment or 'neutral'
            ])

    return response_http


# ============================
# Export ALL PDF Summary
# ============================
@login_required(login_url='/admin_django/login/')
def export_all_pdf(request):
    total_forms     = Form.objects.count()
    total_responses = Response.objects.count()
    all_answers     = ResponseAnswer.objects.filter(field__field_type='text')
    sentiment       = get_sentiment_summary(all_answers)

    response_http = HttpResponse(content_type='application/pdf')
    response_http['Content-Disposition'] = 'attachment; filename="overall_summary_report.pdf"'

    doc = SimpleDocTemplate(response_http, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("Overall Feedback Analytics Summary", styles['Title']))
    elements.append(Spacer(1, 12))

    # Stats Table
    data = [
        ["Metric", "Value"],
        ["Total Forms", str(total_forms)],
        ["Total Responses", str(total_responses)],
        ["Positive Feedback", f"{sentiment['positive']} ({sentiment['positive_pct']}%)"],
        ["Neutral Feedback", f"{sentiment['neutral']} ({sentiment['neutral_pct']}%)"],
        ["Negative Feedback", f"{sentiment['negative']} ({sentiment['negative_pct']}%)"],
    ]
    
    t = Table(data, colWidths=[200, 200])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(t)
    elements.append(Spacer(1, 24))

    # Form Breakdown
    elements.append(Paragraph("Forms Overview", styles['Heading2']))
    form_data = [["Form Title", "Responses", "Created At"]]
    for f in Form.objects.all().order_by('-created_at'):
        count = Response.objects.filter(form=f).count()
        form_data.append([f.title, str(count), f.created_at.strftime('%Y-%m-%d')])
    
    ft = Table(form_data, colWidths=[250, 100, 100])
    ft.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.cadetblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.append(ft)

    doc.build(elements)
    return response_http


# ============================
# Export Single Form PDF
# ============================
@login_required(login_url='/admin_django/login/')
def export_form_pdf(request, form_id):
    form      = get_object_or_404(Form, id=form_id)
    responses = Response.objects.filter(form=form).prefetch_related('answers__field')
    fields    = form.fields.all()
    
    text_answers = ResponseAnswer.objects.filter(field__field_type='text', response__form=form)
    sentiment    = get_sentiment_summary(text_answers)

    response_http = HttpResponse(content_type='application/pdf')
    response_http['Content-Disposition'] = f'attachment; filename="{form.title}_report.pdf"'

    doc = SimpleDocTemplate(response_http, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    elements.append(Paragraph(f"Form Report: {form.title}", styles['Title']))
    elements.append(Paragraph(f"Generated on {form.created_at.strftime('%Y-%m-%d')}", styles['Italic']))
    elements.append(Spacer(1, 12))

    # KPI Table
    kpi_data = [
        ["Total Responses", str(responses.count())],
        ["Positive Sentiment", f"{sentiment['positive_pct']}%"],
        ["Neutral Sentiment", f"{sentiment['neutral_pct']}%"],
        ["Negative Sentiment", f"{sentiment['negative_pct']}%"],
    ]
    kt = Table(kpi_data, colWidths=[200, 100])
    kt.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold')]))
    elements.append(kt)
    elements.append(Spacer(1, 24))

    # Individual Responses
    elements.append(Paragraph("Recent Responses", styles['Heading2']))
    for resp in responses.order_by('-submitted_at')[:20]:  # Limit to 20 for PDF length
        elements.append(Paragraph(f"Response #{resp.id} - {resp.submitted_at.strftime('%Y-%m-%d %H:%M')}", styles['Heading3']))
        
        resp_data = []
        for ans in resp.answers.all():
            resp_data.append([ans.field.label, ans.answer_text])
        
        rt = Table(resp_data, colWidths=[150, 300])
        rt.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.2, colors.lightgrey),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('FONTSIZE', (0,0), (-1,-1), 9)
        ]))
        elements.append(rt)
        elements.append(Spacer(1, 12))

    doc.build(elements)
    return response_http