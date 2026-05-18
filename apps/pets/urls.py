from django.urls import path
from .views import signin_view, signup_view, logout_view, dashboard_view

app_name = 'pets'

urlpatterns = [
    path('', signin_view, name='login'),
    path('signin/', signin_view, name='signin'),
    path('signup/', signup_view, name='signup'),
    path('logout/', logout_view, name='logout'),    
    path('dashboard/', dashboard_view, name='dashboard'),
]