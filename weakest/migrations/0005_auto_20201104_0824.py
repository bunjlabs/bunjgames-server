# Generated by Django 3.1 on 2020-11-04 08:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weakest', '0004_auto_20201102_1029'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='bank_income',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='player',
            name='right_answers',
            field=models.IntegerField(default=0),
        ),
    ]
