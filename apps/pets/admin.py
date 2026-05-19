from django.contrib import admin
from .models import Pet, DailyLog, NutritionLog, Appointment

@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ('name', 'pet_type', 'gender', 'breed', 'owner')
    list_filter = ('pet_type', 'gender', 'owner')

@admin.register(DailyLog)
class DailyLogAdmin(admin.ModelAdmin):
    list_display = ('pet', 'date', 'mood', 'weight_recorded', 'note')
    list_filter = ('pet', 'date', 'mood')

@admin.register(NutritionLog)
class NutritionLogAdmin(admin.ModelAdmin):
    list_display = ('pet', 'date', 'calories_consumed')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'pet', 'due_date', 'is_completed')
    list_filter = ('is_completed', 'due_date')
