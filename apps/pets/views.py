from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from .daily_tip import get_daily_tip
from .daily_tip import TIPS, TIPS_GENERAL
import json

# ดึง Models ที่เราสร้างไว้มาใช้งาน
from .models import Pet, DailyLog, NutritionLog, Appointment
from .utils import get_calendar_context

@login_required
def dashboard_view(request):
    # 1. ดึงสัตว์เลี้ยงทั้งหมดของคนที่ล็อกอินอยู่
    my_pets = Pet.objects.filter(owner=request.user)
    
    # ถ้าผู้ใช้คนนี้ยังไม่มีสัตว์เลี้ยงเลยในระบบ
     # ถ้าไม่มีสัตว์เลี้ยง ส่ง context พร้อม flag ให้ template แสดง empty state
    if not my_pets.exists():
        context = get_calendar_context(request, appointment_dates=set())
        context.update({
            'my_pets': [],        
            'selected_pet': None,
                 
        })
        return render(request, 'pets/dashboard.html', context)

    pet_id = request.GET.get('pet_id')
    selected_pet = get_object_or_404(Pet, id=pet_id, owner=request.user) if pet_id else my_pets.first()

    # 2. เช็กว่าผู้ใช้กดเลือกดูน้องตัวไหนอยู่ (ดึงจากปุ่มกดที่มีการส่ง ?pet_id=... มา)
    # ถ้าไม่มีการส่งมา ให้เลือกน้องตัวแรกสุดเป็นค่าเริ่มต้น (เช่น ตัวแรกคือ Buddy)
    pet_id = request.GET.get('pet_id')
    if pet_id:
        selected_pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    else:
        selected_pet = my_pets.first()

    # 3. ดึงไดอารี่ย้อนหลัง (DailyLog) ของน้องตัวที่เลือก
    daily_logs = DailyLog.objects.filter(pet=selected_pet).order_by('-date')

    # 4. ดึงข้อมูลโภชนาการของ "วันนี้"
    today = date.today()
    nutrition_today_total = NutritionLog.objects.filter(pet=selected_pet, date=today).aggregate(total=Sum('calories_consumed'))['total'] or 0
    
    # จำลองการคำนวณ RER / DER จากน้ำหนักล่าสุด (ดึงน้ำหนักจากไดอารี่ล่าสุด หรือถ้าไม่มีให้ใช้ค่าชั่วคราวภายในคำนวณเท่านั้น)
    latest_log = daily_logs.first()
    latest_weight = latest_log.weight_recorded if latest_log else None
    calculation_weight = latest_weight if latest_weight is not None else 10.0
    
    # สูตรคำนวณพลังงานแบบง่าย (คุณสามารถปรับสูตรตรงนี้ตามที่ตกลงกับกลุ่มได้เลยครับ)
    # RER = 70 * (weight ^ 0.75) หรือคิดแบบง่าย 30 * weight + 70
    rer = int(30 * float(calculation_weight) + 70)
    der = int(rer * 1.6)  # สมมติตัวคูณกิจกรรมปกติ
    
    calories_consumed = nutrition_today_total

    # 5. ดึงรายการนัดหมายทั้งหมดของน้องตัวนี้
    appointments = Appointment.objects.filter(pet=selected_pet).order_by('due_date')
    
    # เอาเฉพาะ "วันที่นัดหมาย (เดย์)" ของเดือนนี้ ไปทำจุดสีส้มบนปฏิทินอัตโนมัติ
    # เช่น นัดวันที่ 2026-05-18 ก็จะดึงเลข 18 ใส่ลงใน Set
    appointment_dates = set(app.due_date.day for app in appointments if app.due_date.month == today.month)

    # 5.1 คำนวณความคืบหน้าโภชนาการ (Nutrition Progress Bar)
    nutrition_percentage = min(int((calories_consumed / der) * 100), 100) if der > 0 else 0

    # 5.2 พลอตกราฟน้ำหนัก (Weight Trend Chart SVG Coordinates)
    recent_logs = list(DailyLog.objects.filter(pet=selected_pet).order_by('-date')[:7])
    logs_for_chart = list(reversed(recent_logs))
    
    weight_svg_path = ""
    weight_svg_area = ""
    weight_svg_dots = []
    weight_svg_labels = []
    
    N = len(logs_for_chart)
    if N > 0:
        weights = [float(log.weight_recorded) for log in logs_for_chart]
        min_w = min(weights)
        max_w = max(weights)
        
        # คำนวณแกน X (ความกว้าง 260px เว้นขอบข้างละ 10px)
        if N > 1:
            x_coords = [10 + i * (240 / (N - 1)) for i in range(N)]
        else:
            x_coords = [130]
            
        # คำนวณแกน Y (ความสูง 100px เว้นขอบบน-ล่างให้สวยงามช่วง [25, 75])
        if max_w == min_w:
            y_coords = [50 for _ in range(N)]
        else:
            y_coords = [75 - ((w - min_w) / (max_w - min_w)) * 50 for w in weights]
            
        # สร้าง Line Path
        weight_svg_path = f"M {x_coords[0]} {y_coords[0]}"
        for i in range(1, N):
            weight_svg_path += f" L {x_coords[i]} {y_coords[i]}"
            
        # สร้าง Area Path
        weight_svg_area = weight_svg_path + f" L {x_coords[-1]} 100 L {x_coords[0]} 100 Z"
        
        # จัดรูปแบบจุดปุ่มกลมบนเส้นกราฟ
        for i in range(N):
            weight_svg_dots.append({
                'x': x_coords[i],
                'y': y_coords[i],
                'is_last': (i == N - 1)
            })
            
        # จัดรูปแบบแกนวันที่
        weight_svg_labels = [f"{log.date.day}/{log.date.month}" for log in logs_for_chart]

    # 6. ดึง Context ปฏิทินตัวเดิมของคุณมาใช้งาน
    context = get_calendar_context(request, appointment_dates=appointment_dates)
    
    # 7. แพ็ครวมข้อมูลทั้งหมดส่งไปให้หน้า HTML เผยแพร่ร่างทรง
    diary_activity_choices = [
        ('walk', 'เดินเล่น', '🚶'),
        ('play', 'เล่นของเล่น', '🎾'),
        ('bath', 'อาบน้ำ', '🛁'),
        ('vet', 'ไปหาหมอ', '🏥'),
        ('rest', 'พักผ่อน', '😴'),
        ('groom', 'ตัดขน', '✂️'),
    ]

    context.update({
        'my_pets': my_pets,
        'selected_pet': selected_pet,
        'daily_logs': daily_logs,
        'calories_consumed': calories_consumed,
        'rer': rer,
        'der': der,
        'nutrition_percentage': nutrition_percentage,
        'appointments': appointments,
        'latest_weight': latest_weight,
        'weight_svg_path': weight_svg_path,
        'weight_svg_area': weight_svg_area,
        'weight_svg_dots': weight_svg_dots,
        'weight_svg_labels': weight_svg_labels,
        'daily_tip': get_daily_tip(selected_pet),
        'diary_activity_choices': diary_activity_choices,
        'meal_choices': [
            {'value': value, 'label': label}
            for value, label in NutritionLog.MEAL_TYPE_CHOICES
        ],
        'selected_calendar_date': request.GET.get('selected_date', ''),
        # pass pool of tips (with {name} replaced) so frontend can rotate every 30s
        'daily_tip_pool_json': json.dumps(
            [t.replace('{name}', f" {selected_pet.name}" if selected_pet and selected_pet.name else '')
             for t in (TIPS.get(selected_pet.pet_type.lower() if selected_pet else '', []) + TIPS_GENERAL)],
            ensure_ascii=False
        ),
    })
    
    return render(request, 'pets/dashboard.html', context)


def signin_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/dashboard/')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'pets/login.html')


def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, 'Please provide username and password')
            return render(request, 'pets/login.html', {'show_signup': True})

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return render(request, 'pets/login.html', {'show_signup': True})

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        return redirect('/dashboard/')

    return render(request, 'pets/login.html', {'show_signup': True})


def logout_view(request):
    logout(request)
    return redirect('/')


@login_required
def profile_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()

        if not username:
            messages.error(request, 'ชื่อผู้ใช้ไม่สามารถว่างได้')
            return redirect('pets:dashboard')

        # ตรวจสอบชื่อผู้ใช้ซ้ำ
        if User.objects.filter(username=username).exclude(id=request.user.id).exists():
            messages.error(request, 'ชื่อผู้ใช้นี้ถูกใช้งานไปแล้ว')
            return redirect('pets:dashboard')

        request.user.username = username
        request.user.email = email

        new_password1 = request.POST.get('new_password1', '')
        new_password2 = request.POST.get('new_password2', '')

        if new_password1 or new_password2:
            if new_password1 != new_password2:
                messages.error(request, 'รหัสผ่านไม่ตรงกัน')
                return redirect('pets:dashboard')
            request.user.set_password(new_password1)
            update_session_auth_hash(request, request.user)

        request.user.save()
        messages.success(request, 'อัปเดตโปรไฟล์เรียบร้อยแล้ว')

    return redirect('pets:dashboard')


@login_required
def edit_pet_view(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    if request.method == 'POST':
        pet.name = request.POST.get('name', '').strip()
        pet.pet_type = request.POST.get('pet_type', 'DOG').strip()
        pet.gender = request.POST.get('gender', 'M').strip()
        pet.breed = request.POST.get('breed', '').strip()
        
        birth_date_str = request.POST.get('birth_date', '')
        if birth_date_str:
            try:
                pet.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'รูปแบบวันเกิดไม่ถูกต้อง')
                return redirect(f'/dashboard/?pet_id={pet.id}')

        pet.save()
        messages.success(request, 'แก้ไขโปรไฟล์สัตว์เลี้ยงเรียบร้อยแล้ว')
        
    return redirect(f'/dashboard/?pet_id={pet.id}')


@login_required
def add_pet_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        pet_type = request.POST.get('pet_type', 'DOG').strip()
        breed = request.POST.get('breed', '').strip()
        gender = request.POST.get('gender', 'M').strip()
        
        pet = Pet(
            owner=request.user,
            name=name,
            pet_type=pet_type,
            breed=breed,
            gender=gender
        )
        
        birth_date_str = request.POST.get('birth_date', '')
        if birth_date_str:
            try:
                pet.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'รูปแบบวันเกิดไม่ถูกต้อง')
                return redirect('pets:dashboard')
                
        pet.save()
        messages.success(request, f'เพิ่ม {pet.name} เข้าสู่ระบบสำเร็จแล้ว')
        return redirect(f'/dashboard/?pet_id={pet.id}')
        
    return redirect('pets:dashboard')


@login_required
def add_daily_log_view(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    if request.method == 'POST':
        date_str = request.POST.get('date', '')
        note = request.POST.get('note', '').strip()
        weight_str = request.POST.get('weight', '').strip()

        # Get the latest weight recorded from previous daily logs as fallback
        latest_log = DailyLog.objects.filter(pet=pet).order_by('-date').first()
        try:
            weight_recorded = Decimal(weight_str) if weight_str else (latest_log.weight_recorded if latest_log else Decimal('10.0'))
        except (InvalidOperation, ValueError):
            weight_recorded = latest_log.weight_recorded if latest_log else Decimal('10.0')

        try:
            log_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
        except ValueError:
            log_date = date.today()

        DailyLog.objects.create(
            pet=pet,
            date=log_date,
            weight_recorded=weight_recorded,
            note=note if note else "บันทึกประจำวันทั่วไป"
        )
        messages.success(request, 'เพิ่มบันทึกไดอารี่เรียบร้อยแล้ว')
    return redirect(f'/dashboard/?pet_id={pet.id}')


@login_required
def edit_daily_log_view(request, pet_id, log_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    log = get_object_or_404(DailyLog, id=log_id, pet=pet)
    if request.method == 'POST':
        date_str = request.POST.get('date', '')
        note = request.POST.get('note', '').strip()
        weight_str = request.POST.get('weight', '').strip()

        try:
            log_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
        except ValueError:
            log_date = date.today()

        log.date = log_date
        log.note = note if note else "บันทึกประจำวันทั่วไป"
        try:
            if weight_str:
                log.weight_recorded = Decimal(weight_str)
        except (InvalidOperation, ValueError):
            pass
        log.save()
        messages.success(request, 'แก้ไขบันทึกไดอารี่เรียบร้อยแล้ว')
    return redirect(f'/dashboard/?pet_id={pet.id}')


@login_required
def delete_daily_log_view(request, pet_id, log_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    log = get_object_or_404(DailyLog, id=log_id, pet=pet)
    if request.method == 'POST':
        log.delete()
        messages.success(request, 'ลบบันทึกไดอารี่เรียบร้อยแล้ว')
    return redirect(f'/dashboard/?pet_id={pet.id}')


@login_required
def add_nutrition_log_view(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    if request.method == 'POST':
        date_str = request.POST.get('date', '')
        meal_type = request.POST.get('meal_type', 'morning').strip()
        food_name = request.POST.get('food_name', '').strip()
        amount_str = request.POST.get('amount', '').strip()
        unit = request.POST.get('unit', '').strip()
        calories_str = request.POST.get('calories', '')
        note = request.POST.get('note', '').strip()
        
        try:
            log_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
        except ValueError:
            log_date = date.today()

        if meal_type not in dict(NutritionLog.MEAL_TYPE_CHOICES):
            meal_type = 'morning'

        try:
            amount = Decimal(amount_str) if amount_str else Decimal('0')
        except (InvalidOperation, ValueError):
            amount = Decimal('0')
            
        try:
            calories = int(calories_str) if calories_str else 0
        except ValueError:
            calories = 0

        NutritionLog.objects.create(
            pet=pet,
            date=log_date,
            meal_type=meal_type,
            food_name=food_name,
            amount=amount,
            unit=unit,
            calories_consumed=calories,
            note=note,
        )

        messages.success(request, 'บันทึกโภชนาการเรียบร้อยแล้ว')
    return redirect(f'/dashboard/?pet_id={pet.id}')
@login_required
def add_appointment(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    if request.method == 'POST':
        title    = request.POST.get('title', '').strip()
        due_date = request.POST.get('due_date')
        time     = request.POST.get('time') or None
        note     = request.POST.get('note', '').strip()
        due_date_obj = None

        if due_date:
            try:
                due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
            except ValueError:
                due_date_obj = None

        if title and due_date:
            Appointment.objects.create(
                pet=pet, title=title, due_date=due_date, time=time, note=note,
            )
        if due_date_obj:
            return redirect(
                f'/dashboard/?pet_id={pet.id}&year={due_date_obj.year}&month={due_date_obj.month}&selected_date={due_date_obj.isoformat()}'
            )

    return redirect(f'/dashboard/?pet_id={pet.id}')


@login_required
def toggle_appointment(request, pet_id, appointment_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    appointment = get_object_or_404(Appointment, id=appointment_id, pet=pet)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        appointment.is_completed = not appointment.is_completed
        appointment.save(update_fields=['is_completed'])

        if is_ajax:
            return JsonResponse({
                'success': True,
                'is_completed': appointment.is_completed,
            })

        next_url = request.POST.get('next', '').strip()
        if next_url.startswith('/'):
            return redirect(next_url)

    if is_ajax:
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    return redirect(f'/dashboard/?pet_id={pet.id}')