# Generated by Django 4.1.1 on 2022-09-17 13:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meeting_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Meeting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.AddField(
            model_name='profile',
            name='time_zone',
            field=models.CharField(blank=True, default='Asia/Kolkata', max_length=256, null=True),
        ),
    ]
