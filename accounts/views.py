from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView, LoginView
from django.core.exceptions import PermissionDenied
from .models import CustomUser
from .forms import CustomUserChangeForm, CustomUserCreationForm, CustomPasswordChangeForm, CustomAuthenticationForm
from django.db.models import Q

# アカウント関連
class SignUpView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:login')

class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'

class CustomUserListView(LoginRequiredMixin, ListView):
    model = CustomUser
    template_name = 'accounts/profile_list.html'
    paginate_by = 10

    def get_queryset(self):
        queryset = CustomUser.objects.all().order_by('pk')
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(username__icontains=q) | Q(full_name__icontains=q) | Q(email__icontains=q)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        return context

class CustomUserDetailView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'accounts/profile_detail.html'

class CustomUserUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'accounts/profile_update.html'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj != self.request.user:
            raise PermissionDenied
        return obj
    
    def get_success_url(self):
        return reverse('accounts:profile_detail', kwargs={'pk': self.object.pk})

class CustomUserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = CustomUser
    template_name = 'accounts/profile_delete.html'
    success_url = reverse_lazy('accounts:profile_list')
    #　管理者のみ許可
    def test_func(self):
        return self.request.user.is_superuser

# パスワード変更処理
class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:password_change_done')

class CustomPasswordChangeDoneView(LoginRequiredMixin, PasswordChangeDoneView):
    template_name = 'accounts/password_change_done.html'