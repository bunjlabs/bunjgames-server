# Generated by Django 3.1 on 2020-10-20 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('whirligig', '0004_auto_20201013_1232'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='state',
            field=models.CharField(choices=[('start', 'start'), ('intro', 'intro'), ('questions', 'questions'), ('question_whirligig', 'question_whirligig'), ('question_start', 'question_start'), ('question_discussion', 'question_discussion'), ('answer', 'answer'), ('extra_minute', 'extra_minute'), ('club_help', 'club_help'), ('right_answer', 'right_answer'), ('question_end', 'question_end'), ('end', 'end')], default='start', max_length=25),
        ),
    ]
