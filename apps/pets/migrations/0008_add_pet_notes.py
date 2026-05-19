from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pets', '0007_add_pet_calorie_goal'),
    ]

    operations = [
        migrations.AddField(
            model_name='pet',
            name='notes',
            field=models.TextField(blank=True, default='', verbose_name='โน้ตเพิ่มเติม'),
        ),
    ]
