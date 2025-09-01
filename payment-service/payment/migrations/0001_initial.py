# Generated manually for payment service
# This creates the necessary database tables

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('payment_id', models.AutoField(primary_key=True, serialize=False)),
                ('payment_uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('order_uuid', models.UUIDField()),
                ('user_uuid', models.UUIDField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_method', models.SmallIntegerField(choices=[(0, 'alipay'), (1, 'wechat_pay')])),
                ('status', models.SmallIntegerField(choices=[(0, 'pending'), (1, 'processing'), (2, 'success'), (3, 'failed'), (4, 'cancelled')], default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('transaction_id', models.BigIntegerField(blank=True, null=True)),
                ('payment_subject', models.CharField(max_length=255)),
                ('payment_data', models.JSONField(blank=True, default=dict)),
                ('failure_reason', models.CharField(blank=True, max_length=255, null=True)),
                ('callback_received', models.BooleanField(default=False)),
                ('callback_data', models.JSONField(blank=True, default=dict)),
                ('callback_time', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'payment',
                'ordering': ['-created_at'],
            },
        ),
    ]
