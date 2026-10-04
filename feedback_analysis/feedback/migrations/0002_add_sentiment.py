
from django.db import migrations, models


class Migration(migrations.Migration):

    # ⚠️ Change '0001_initial' to your actual last migration name
    dependencies = [
        ('feedback', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='responseanswer',
            name='sentiment',
            field=models.CharField(
                blank=True,
                choices=[
                    ('positive', 'Positive'),
                    ('neutral',  'Neutral'),
                    ('negative', 'Negative'),
                ],
                max_length=10,
                null=True,
            ),
        ),
    ]