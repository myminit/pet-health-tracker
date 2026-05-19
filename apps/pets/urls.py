from django.urls import path
from .views import signin_view, signup_view, logout_view, dashboard_view
from .views import profile_view, edit_pet_view, add_pet_view, add_daily_log_view, edit_daily_log_view, delete_daily_log_view, add_nutrition_log_view

app_name = 'pets'

urlpatterns = [
    path('', signin_view, name='login'),
    path('signin/', signin_view, name='signin'),
    path('signup/', signup_view, name='signup'),
    path('logout/', logout_view, name='logout'),    
    path('dashboard/', dashboard_view, name='dashboard'),
    path('profile/', profile_view, name='profile'),
    path('pet/add/', add_pet_view, name='add_pet'),
    path('pet/<int:pet_id>/edit/', edit_pet_view, name='edit_pet'),
    path('pet/<int:pet_id>/daily_log/add/', add_daily_log_view, name='add_daily_log'),
    path('pet/<int:pet_id>/daily_log/<int:log_id>/edit/', edit_daily_log_view, name='edit_daily_log'),
    path('pet/<int:pet_id>/daily_log/<int:log_id>/delete/', delete_daily_log_view, name='delete_daily_log'),
    path('pet/<int:pet_id>/nutrition/add/', add_nutrition_log_view, name='add_nutrition_log'),
]