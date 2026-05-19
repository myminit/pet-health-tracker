from django.db import models
from django.contrib.auth.models import User 

# ==========================================
# 1. MODEL: สัตว์เลี้ยง (Pet)
# ==========================================
class Pet(models.Model):
    PET_TYPE_CHOICES = [
        ('DOG', 'สุนัข'),
        ('CAT', 'แมว'),
        ('RABBIT', 'กระต่าย'),
        ('OTHER', 'อื่นๆ'),
    ]

    GENDER_CHOICES = [
        ('M', '♂ ผู้'),
        ('F', '♀ เมีย'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pets', verbose_name="เจ้าของ")
    name = models.CharField(max_length=100, verbose_name="ชื่อสัตว์เลี้ยง")
    pet_type = models.CharField(max_length=10, choices=PET_TYPE_CHOICES, default='DOG', verbose_name="ประเภทสัตว์เลี้ยง")
    gender = models.CharField(max_length=2, choices=GENDER_CHOICES, default='M', verbose_name="เพศ")
    breed = models.CharField(max_length=100, blank=True, null=True, verbose_name="สายพันธุ์")
    birth_date = models.DateField(verbose_name="วันเกิด")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "สัตว์เลี้ยง"
        verbose_name_plural = "ข้อมูลสัตว์เลี้ยง"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.name} ({self.get_pet_type_display()})"


# ==========================================
# 2. MODEL: ไดอารี่ประจำวันและน้ำหนัก (DailyLog)
# ==========================================
class DailyLog(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='daily_logs', verbose_name="สัตว์เลี้ยง")
    date = models.DateField(verbose_name="วันที่บันทึก")
    note = models.TextField(verbose_name="บันทึกกิจกรรมประจำวัน")
    
    # เก็บค่าน้ำหนักแยกตามวัน เพื่อเอาไปวาดกราฟ "แนวโน้มน้ำหนัก"
    weight_recorded = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="น้ำหนักที่ชั่งได้ (กก.)")
    
    mood = models.CharField(max_length=20, blank=True, null=True, verbose_name="อารมณ์")
    
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def mood_emoji(self):
        mood_map = {
            'very_happy': '😄',
            'happy': '😊',
            'normal': '😐',
            'sad': '😢',
            'sick': '🤒',
        }
        return mood_map.get(self.mood, '📝')

    class Meta:
        verbose_name = "ไดอารี่ประจำวัน"
        verbose_name_plural = "บันทึกไดอารี่ประจำวัน"
        ordering = ['-date']  # เรียงจากวันที่ล่าสุดขึ้นก่อนตามหน้าจอ UI

    def __str__(self):
        return f"บันทึกของ {self.pet.name} วันที่ {self.date}"


# ==========================================
# 3. MODEL: บันทึกโภชนาการและการกิน (NutritionLog)
# ==========================================
class NutritionLog(models.Model):
    MEAL_TYPE_CHOICES = [
        ('morning', 'เช้า'),
        ('noon', 'กลางวัน'),
        ('evening', 'เย็น'),
        ('snack', 'ของว่าง'),
    ]

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='nutrition_logs', verbose_name="สัตว์เลี้ยง")
    date = models.DateField(verbose_name="วันที่กิน")
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES, default='morning', verbose_name="มื้ออาหาร")
    food_name = models.CharField(max_length=200, verbose_name="ชื่ออาหาร")
    amount = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="ปริมาณ")
    unit = models.CharField(max_length=20, verbose_name="หน่วย")
    note = models.TextField(blank=True, default="", verbose_name="หมายเหตุ")
    
    # จำนวนแคลอรีที่น้องกินเข้าไปจริงๆ ในวันนั้น (เอาไปคำนวณแถบ Progress bar สีส้ม)
    calories_consumed = models.IntegerField(default=0, verbose_name="แคลอรีที่กินไป (kcal)")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "บันทึกการกิน"
        verbose_name_plural = "บันทึกโภชนาการประจำวัน"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"โภชนาการของ {self.pet.name} ({self.date}) - {self.food_name}"


# ==========================================
# 4. MODEL: รายการนัดหมายและกิจกรรม (Appointment)
# ==========================================
class Appointment(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='appointments', verbose_name="สัตว์เลี้ยง")
    title = models.CharField(max_length=200, verbose_name="หัวข้อนัดหมาย/กิจกรรม")
    due_date = models.DateField(verbose_name="วันที่นัดหมาย")
    time = models.TimeField(blank=True, null=True, verbose_name="เวลา")
    note = models.TextField(blank=True, default="", verbose_name="หมายเหตุ")
    
    # สถานะว่าทำกิจกรรมนี้สำเร็จหรือยัง (True = ติ๊กถูกสีส้มบนจอ / False = วงกลมว่างๆ)
    is_completed = models.BooleanField(default=False, verbose_name="ทำสำเร็จแล้ว")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "นัดหมาย"
        verbose_name_plural = "รายการนัดหมายและกิจกรรม"
        ordering = ['due_date']

    def __str__(self):
        status = "ทำแล้ว" if self.is_completed else "ยังไม่ทำ"
        return f"[{status}] {self.title} - {self.pet.name} ({self.due_date})"