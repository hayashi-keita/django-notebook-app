from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('profiles/', views.CustomUserListView.as_view(), name='profile_list'),
    path('profile/<int:pk>/detail/', views.CustomUserDetailView.as_view(), name='profile_detail'),
    path('profile/<int:pk>/update/', views.CustomUserUpdateView.as_view(), name='profile_update'),
    path('profile/<int:pk>/delete/', views.CustomUserDeleteView.as_view(), name='profile_delete'),
    path('password_change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('password_change_done/', views.CustomPasswordChangeDoneView.as_view(), name='password_change_done'),
]