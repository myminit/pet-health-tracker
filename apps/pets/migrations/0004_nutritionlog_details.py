from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pets', '0003_dailylog_mood'),
    ]

    operations = [
        migrations.AddField(
            model_name='nutritionlog',
            name='meal_type',
            field=models.CharField(choices=[('morning', 'เช้า'), ('noon', 'กลางวัน'), ('evening', 'เย็น'), ('snack', 'ของว่าง')], default='morning', max_length=20, verbose_name='มื้ออาหาร'),
        ),
        migrations.AddField(
            model_name='nutritionlog',
            name='food_name',
            field=models.CharField(default='', max_length=200, verbose_name='ชื่ออาหาร'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='nutritionlog',
            name='amount',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=8, verbose_name='ปริมาณ'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='nutritionlog',
            name='unit',
            field=models.CharField(default='', max_length=20, verbose_name='หน่วย'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='nutritionlog',
            name='note',
            field=models.TextField(blank=True, default='', verbose_name='หมายเหตุ'),
        ),
        migrations.AlterModelOptions(
            name='nutritionlog',
            options={'ordering': ['-date', '-created_at'], 'verbose_name': 'บันทึกการกิน', 'verbose_name_plural': 'บันทึกโภชนาการประจำวัน'},
        ),
        migrations.AlterUniqueTogether(
            name='nutritionlog',
            unique_together=set(),
        ),
    ]