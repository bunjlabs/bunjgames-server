# Generated by Django 3.1 on 2020-11-04 09:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weakest', '0005_auto_20201104_0824'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='strongest',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='weakest.player'),
        ),
        migrations.AddField(
            model_name='game',
            name='weakest',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='weakest.player'),
        ),
    ]