# FeedbackIQ – AI-Powered Feedback Analysis Platform

> An intelligent feedback collection and automated sentiment analysis platform built with Django. FeedbackIQ allows teams to generate dynamic feedback forms, process responses with TextBlob and Groq LLMs in real time, monitor live sentiment metrics, and export executive-ready CSV and PDF reports.

---

## Badges

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2+-092E20?style=flat&logo=django&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-Llama--3.3--70B-F05032?style=flat)
![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat)

---

## Features

- **Dynamic Form Builder**: Create customized feedback forms with text, number, and dropdown questions via Django Admin.
- **Unique Shareable URLs & QR Codes**: Each form receives a dedicated UUID link (`/form/<uuid>/`) and one-click QR code/link sharing.
- **Real-Time Sentiment Classification**: Automatically evaluates text responses into Positive, Neutral, or Negative classifications using TextBlob polarity analysis.
- **LLM Insights with Groq (`llama-3.3-70b-versatile`)**: Automatically extracts key product/service issues, positive highlights, and constructive suggestions per response and per form.
- **Configurable Numerical Analytics**: Toggle statistical calculations (`calculate_stats`) per numerical field to compute averages, min, and max while skipping identifiers (e.g., phone numbers).
- **Interactive Analytics Dashboard**: Visualizes response timelines, sentiment trends, recent submission activity, and field distribution charts using Chart.js.
- **Multi-Format Exporting**: Generate on-demand CSV files and formatted PDF reports (via ReportLab) for individual forms or bulk aggregate datasets.
- **Modern Dark-Mode UI**: Custom glassmorphism-styled admin interface and dashboards crafted with Vanilla CSS and Bootstrap Icons.

---

## Tech Stack

- **Backend Framework**: Python 3.11+, Django 5.2
- **Database**: SQLite (`db.sqlite3`)
- **AI & NLP**: 
  - [Groq SDK](https://github.com/groq/groq-python) (`llama-3.3-70b-versatile`) for deep insight and issue extraction
  - [TextBlob](https://textblob.readthedocs.io/) for fast sentiment polarity scoring
- **Document & Data Processing**: ReportLab (PDF generation), Pandas
- **Frontend & UI**: HTML5, Vanilla CSS (Glassmorphism design system), Bootstrap Icons, Chart.js (CDN)

---

## How It Works

1. **Form Creation**: The admin defines form fields (Text, Rating/Number, Dropdown) and retrieves the unique public URL.
2. **User Submission**: Respondents access the public link and submit their feedback.
3. **Sentiment & AI Pipeline**: `sentiment_utils.py` computes polarity scores via TextBlob and calls Groq's LLaMA 3.3 model to parse issues, positive remarks, and recommendations into structured JSON.
4. **Data Persistence**: Answers, sentiment labels, and AI-generated insights are saved directly to `ResponseAnswer` records in SQLite.
5. **Visualization & Reporting**: The admin views live metrics on the dashboard, explores detailed feedback records, and downloads CSV/PDF summaries.

```text
[ Respondent ] ──> ( Public Form URL )
                           │
                           ▼
                 [ Django Views (submit_form) ]
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
    [ TextBlob Polarity ]      [ Groq LLaMA 3.3 LLM ]
    (Positive/Neutral/Negative)  (Issues, Positives, Suggestions)
             │                           │
             └─────────────┬─────────────┘
                           ▼
               [ SQLite Database Storage ]
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
   [ Interactive Dashboards ]    [ PDF / CSV Reports ]
```

---

## Project Structure

```text
Feedback Analysis project/
├── .gitignore                      # Git ignore rules for virtual environments, sqlite, and cache
├── README.md                       # Comprehensive project documentation
└── feedback_analysis/              # Root Django project folder
    ├── manage.py                   # Django management script
    ├── requirements.txt            # Project dependencies and pinned library versions
    ├── .env.example                # Sample environment variable template
    ├── .env                        # Local secrets configuration (ignored in git)
    ├── db.sqlite3                  # SQLite database instance
    ├── feedback_analysis/          # Project configuration package
    │   ├── __init__.py
    │   ├── asgi.py                 # ASGI configuration for async deployment
    │   ├── settings.py             # Django settings, apps, middleware, and AI configuration
    │   ├── urls.py                 # Root URL configuration and route delegator
    │   └── wsgi.py                 # WSGI configuration for production servers
    └── feedback/                   # Core feedback application
        ├── admin.py                # Custom Django Admin configuration with QR modals & submission views
        ├── apps.py                 # App configuration for feedback app
        ├── models.py               # Database schemas (Form, FormField, Response, ResponseAnswer)
        ├── sentiment_utils.py      # TextBlob sentiment scoring and Groq LLM integration logic
        ├── tests.py                # Test suite module
        ├── urls.py                 # Application route endpoints
        ├── views.py                # Core application logic, analytics controllers, and PDF/CSV exporters
        ├── migrations/             # Database migration history files
        └── templates/              # HTML templates
            ├── admin/              # Styled admin panel overrides and submission viewers
            └── feedback/           # Public forms, thank you page, dashboard, and report views
```

---

## Installation and Setup

### Prerequisites
- Python 3.11 or higher installed
- Git installed
- A free [Groq Cloud API Key](https://console.groq.com/)

### 1. Clone the Repository
```bash
git clone https://github.com/siddhu9009/Feedback-Analysis-project.git
cd "Feedback Analysis project"
```

### 2. Set Up a Virtual Environment

**On Windows (PowerShell / Command Prompt):**
```powershell
cd feedback_analysis
python -m venv venv
.\venv\Scripts\activate
```

**On Linux / macOS:**
```bash
cd feedback_analysis
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` in the `feedback_analysis` directory:

**Windows:**
```powershell
copy .env.example .env
```

**Linux / macOS:**
```bash
cp .env.example .env
```

Open `.env` in your editor and provide your credentials:
```env
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
SECRET_KEY=your_django_secret_key_here
```

### 5. Apply Database Migrations
```bash
python manage.py migrate
```

### 6. Create Superuser (Admin Access)
```bash
python manage.py createsuperuser
```
Follow the prompts to configure your admin username, email, and password.

### 7. Start the Development Server
```bash
python manage.py runserver
```

Open your browser and navigate to `http://127.0.0.1:8000/`.

---

## Environment Variables

The application reads configuration settings from `feedback_analysis/.env`:

| Variable | Description | Example Value |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | API key from Groq Console used for LLaMA 3.3 insight analysis | `gsk_AbCdEf1234567890xyz` |
| `SECRET_KEY` | Django cryptographic secret key | `django-insecure-example-key-12345` |
| `DEBUG` *(Optional)* | Toggles debug mode (defaults to `True` if omitted) | `True` or `False` |

---

## Usage & Routes

| Route | Description | Authentication |
| :--- | :--- | :--- |
| `/admin/` | Executive Analytics Dashboard with sentiment breakdowns and activity feeds | Required (`login_required`) |
| `/admin_django/` | Standard Django admin interface for creating forms, managing fields, and viewing raw submissions | Required (Staff/Superuser) |
| `/forms/` | Overview listing of all created feedback forms with AI summaries | Required (`login_required`) |
| `/form/<uuid:unique_code>/` | Public feedback submission page for end users | Public |
| `/dashboard/<int:form_id>/` | Detailed per-form analytics dashboard with charts and sentiment stats | Required (`login_required`) |
| `/reports/` | Consolidated reports overview for all forms | Required (`login_required`) |
| `/reports/<int:form_id>/` | Comprehensive tabular response viewer for an individual form | Required (`login_required`) |
| `/reports/<int:form_id>/download/` | Exports responses for a single form as a CSV file | Required (`login_required`) |
| `/reports/<int:form_id>/download/pdf/`| Generates a formatted PDF report for a single form | Required (`login_required`) |
| `/export/all/csv/` | Exports all responses across all forms as a consolidated CSV | Required (`login_required`) |
| `/export/all/pdf/` | Generates a high-level executive PDF summary of all platform feedback | Required (`login_required`) |

---

## Screenshots

<!-- Add your application screenshots inside a screenshots/ directory in the project root -->

### Executive Dashboard
![Executive Dashboard](screenshots/dashboard.png)

### Public Feedback Form
![Public Form](screenshots/public_form.png)

### Form Analytics & Charts
![Analytics Overview](screenshots/analytics.png)

### Form Management & AI Summaries
![Forms List](screenshots/forms_list.png)

---

## Running Tests

To run the Django test suite:

```bash
python manage.py test
```

> **Note**: `feedback/tests.py` is configured and ready for additional unit and integration tests covering form creation, response ingestion, and PDF rendering.

---

## Future Improvements

1. **Asynchronous AI Processing**: Integrate Celery with Redis to process Groq LLM queries in the background so public form submission responses return instantly.
2. **Multi-Tenant User Accounts**: Implement creator-level user authentication so non-staff users can manage their own independent feedback forms.
3. **Automated Notification Webhooks**: Dispatch automated email or Slack/Discord alerts when negative feedback or critical product issues are detected.
4. **Expanded Unit & Integration Tests**: Implement automated test cases for sentiment classification, form validation, and export generators.
5. **Customizable Rating Types**: Add Star Ratings, NPS (Net Promoter Score 1–10) scales, and Likert scale form field widgets.

---

## Author

**Siddharth Ravindra Khot**  
GitHub: [@siddhu9009](https://github.com/siddhu9009)

---

## License

This project is licensed under the [MIT License](LICENSE).
