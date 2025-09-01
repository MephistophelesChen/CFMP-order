# Generated manually for order service
# This creates the necessary database tables

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('order_id', models.AutoField(primary_key=True, serialize=False)),
                ('order_uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('buyer_uuid', models.UUIDField()),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.SmallIntegerField(choices=[(0, 'pending_payment'), (1, 'paid'), (2, 'completed'), (3, 'cancelled')], default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('payment_method', models.SmallIntegerField(blank=True, choices=[(0, 'alipay'), (1, 'wechat_pay')], null=True)),
                ('payment_time', models.DateTimeField(blank=True, null=True)),
                ('remark', models.TextField(blank=True, null=True)),
                ('cancel_reason', models.TextField(blank=True, null=True)),
                ('shipping_name', models.CharField(blank=True, max_length=500, null=True)),
                ('shipping_phone', models.CharField(blank=True, max_length=200, null=True)),
                ('shipping_address', models.TextField(blank=True, null=True)),
                ('shipping_postal_code', models.CharField(blank=True, max_length=20, null=True)),
            ],
            options={
                'db_table': 'order',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_uuid', models.UUIDField()),
                ('product_name', models.CharField(max_length=255)),
                ('product_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('product_image', models.URLField(blank=True, null=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_items', to='order.order')),
            ],
            options={
                'db_table': 'order_item',
            },
        ),
    ]
