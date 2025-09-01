# Generated manually for notification service
# This creates the necessary database tables

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('notification_uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('user_uuid', models.UUIDField()),
                ('type', models.SmallIntegerField(choices=[(0, 'transaction'), (1, 'system'), (2, 'promotion')])),
                ('title', models.CharField(max_length=100)),
                ('content', models.TextField()),
                ('read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('related_id', models.CharField(blank=True, max_length=50, null=True)),
                ('related_data', models.JSONField(blank=True, default=dict, null=True)),
            ],
            options={
                'db_table': 'notification',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SecurityPolicy',
            fields=[
                ('policy_id', models.IntegerField(primary_key=True, serialize=False)),
                ('policy_uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('policy_name', models.CharField(max_length=100)),
                ('policy_description', models.TextField()),
                ('is_enabled', models.BooleanField(default=True)),
                ('security_level', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('config_data', models.JSONField(default=dict)),
            ],
            options={
                'db_table': 'security_policy',
            },
        ),
        migrations.CreateModel(
            name='RiskAssessment',
            fields=[
                ('assessment_id', models.AutoField(primary_key=True, serialize=False)),
                ('assessment_uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('user_uuid', models.UUIDField()),
                ('order_uuid', models.UUIDField(blank=True, null=True)),
                ('risk_score', models.FloatField()),
                ('risk_level', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], max_length=20)),
                ('assessment_data', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_processed', models.BooleanField(default=False)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('action_taken', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'risk_assessment',
                'ordering': ['-created_at'],
            },
        ),
    ]
