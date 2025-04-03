from django.shortcuts import render

#custom
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from .forms import ProfileUpdateForm, AdminUserCreateForm, AdminUserUpdateForm
from django.contrib.auth import get_user_model
from .decorators import admin_required
from django.http import JsonResponse
from django.template.loader import render_to_string

User = get_user_model()

# Create your views here.
@login_required
def home(request):
    return render(request, 'home.html')

def login_page(request):
    error = None
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('/')  # Giriş sonrası yönlendirme
        else:
            error = "Kullanıcı adı veya şifre yanlış."
    return render(request, 'accounts/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil başarıyla güncellendi.")
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'accounts/edit_profile.html', {'form': form})

@admin_required
def user_list(request):
    users = User.objects.all()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = []
        for user in users:
            team_name = user.team.name if user.team else '-'
            data.append({
                'id': user.id,
                'username': user.username,
                'full_name': user.get_full_name(),
                'email': user.email,
                'team': team_name
            })
        return JsonResponse({'users': data})
    
    return render(request, 'accounts/user_list.html', {'users': users})

@admin_required
def create_user(request):
    if request.method == 'POST':
        form = AdminUserCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Kullanıcı başarıyla oluşturuldu.'})
            
            return redirect('user_list')
    else:
        form = AdminUserCreateForm()
    
    context = {
        'form': form, 
        'title': 'Yeni Kullanıcı Ekle',
        'is_ajax': request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('accounts/user_form.html', context, request=request)
        return JsonResponse({'html': html})
    
    return render(request, 'accounts/user_form.html', context)

@admin_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    form = AdminUserUpdateForm(request.POST or None, instance=user)
    
    if request.method == 'POST' and form.is_valid():
        form.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Kullanıcı başarıyla güncellendi.'})
        
        return redirect('user_list')
    
    context = {
        'form': form, 
        'title': 'Kullanıcıyı Güncelle',
        'is_ajax': request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('accounts/user_form.html', context, request=request)
        return JsonResponse({'html': html})
    
    return render(request, 'accounts/user_form.html', context)

@admin_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Kullanıcı başarıyla silindi.'})
    
    return redirect('user_list')
