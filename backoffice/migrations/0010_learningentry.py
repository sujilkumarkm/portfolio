from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('backoffice', '0009_visitor_ip_address_visitor_last_seen_visitor_visits'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(
        name='LearningEntry',
        fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('date', models.DateField()),
            ('draft', models.JSONField(default=list)),
            ('ideas', models.JSONField(default=list)),
            ('saved_at', models.DateTimeField(blank=True, null=True)),
            ('updated_at', models.DateTimeField(auto_now=True)),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
        ],
        options={'ordering': ['-date'], 'constraints': [models.UniqueConstraint(fields=('user', 'date'), name='one_learning_day_per_user')]},
    )]
