from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0002_alter_form_description'),
    ]

    operations = [
        # Only adding calculate_stats — sentiment already exists from previous migration
        migrations.AddField(
            model_name='formfield',
            name='calculate_stats',
            field=models.BooleanField(
                default=True,
                help_text="Uncheck for phone numbers, vehicle numbers — skips average/min/max calculation"
            ),
        ),
    ]