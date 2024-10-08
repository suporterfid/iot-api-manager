# Generated by Django 4.2.16 on 2024-09-06 16:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smartreader', '0002_remove_smartreader_field_delim_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='smartreader',
            name='mqtt_control_response_retain_messages',
        ),
        migrations.RemoveField(
            model_name='smartreader',
            name='mqtt_management_response_retain_messages',
        ),
        migrations.RemoveField(
            model_name='smartreader',
            name='mqtt_metric_events_retain_messages',
        ),
        migrations.AddField(
            model_name='smartreader',
            name='barcode_no_data_string',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='smartreader',
            name='field_delim',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='smartreader',
            name='line_end',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='smartreader',
            name='mqtt_broker_protocol',
            field=models.CharField(blank=True, default='/mqtt', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='smartreader',
            name='mqtt_broker_type',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='smartreader',
            name='csv_file_format',
            field=models.IntegerField(default=False),
        ),
    ]
