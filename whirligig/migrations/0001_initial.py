# Generated by Django 3.1 on 2020-08-30 07:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=25, unique=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('expired', models.DateTimeField()),
                ('connoisseurs_score', models.IntegerField(default=0)),
                ('viewers_score', models.IntegerField(default=0)),
                ('cur_item', models.IntegerField(default=None, null=True)),
                ('cur_question', models.IntegerField(default=None, null=True)),
                ('state', models.CharField(blank=True, choices=[('start', 'start'), ('intro', 'intro'), ('questions', 'questions'), ('question_start', 'question_start'), ('question_discussion', 'question_discussion'), ('question_end', 'question_end'), ('end', 'end')], default='start', max_length=25)),
                ('hash', models.CharField(blank=True, default='', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='GameItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('name', models.CharField(max_length=255)),
                ('description', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[('standard', 'standard'), ('blitz', 'blitz'), ('superblitz', 'superblitz')], max_length=25)),
                ('is_processed', models.BooleanField(blank=True, default=False)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='whirligig.game')),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('is_processed', models.BooleanField(blank=True, default=False)),
                ('description', models.TextField()),
                ('text', models.TextField(null=True)),
                ('image', models.CharField(max_length=255, null=True)),
                ('audio', models.CharField(max_length=255, null=True)),
                ('video', models.CharField(max_length=255, null=True)),
                ('answer_description', models.TextField()),
                ('answer_text', models.TextField(null=True)),
                ('answer_image', models.CharField(max_length=255, null=True)),
                ('answer_audio', models.CharField(max_length=255, null=True)),
                ('answer_video', models.CharField(max_length=255, null=True)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='whirligig.gameitem')),
            ],
        ),
        migrations.AddIndex(
            model_name='game',
            index=models.Index(fields=['token'], name='whirligig_g_token_1edb94_idx'),
        ),
    ]
