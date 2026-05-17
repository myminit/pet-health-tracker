from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages


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