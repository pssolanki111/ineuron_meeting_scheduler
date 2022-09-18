# Generated by Django 4.1.1 on 2022-09-17 17:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('meeting_app', '0003_availableslot_bookedmeeting_sharelink_delete_meeting'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='sharelink',
            options={'verbose_name': 'Share Link', 'verbose_name_plural': 'Share Links'},
        ),
        migrations.AddField(
            model_name='bookedmeeting',
            name='booked_with_link',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.PROTECT, to='meeting_app.sharelink'),
            preserve_default=False,
        ),
    ]
