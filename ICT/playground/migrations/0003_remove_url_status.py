# Generated by Django 4.1.2 on 2022-11-05 08:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('playground', '0002_alter_url_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='url',
            name='status',
        ),
    ]