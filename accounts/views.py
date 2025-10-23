from asyncio import QueueEmpty
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView, LoginView
from .models import CustomUser
from .forms import CustomUserChangeForm, CustomUserCreationForm, CustomPasswordChangeForm, CustomAuthenticationForm, UserSelfUpdateForm
from .mixins import AdminOnlyMixin, TeacherAndAdminOnlyMixin, UserIsOwnerOrStaffMixin, UserIsOwnerOrAdminMixin
from django.db.models import Q

# アカウント関連
class SignUpView(AdminOnlyMixin, CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:profile_list')

class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'

class CustomUserListView(TeacherAndAdminOnlyMixin, ListView):
    model = CustomUser
    template_name = 'accounts/profile_list.html'
    paginate_by = 10

    def get_queryset(self):
        queryset = CustomUser.objects.all().order_by('pk')
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(username__icontains=q) | Q(full_name__icontains=q)
            )
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role=role)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['role'] = self.request.GET.get('role', '')
        return context

class CustomUserDetailView(UserIsOwnerOrStaffMixin, DetailView):
    model = CustomUser
    template_name = 'accounts/profile_detail.html'

class CustomUserUpdateView(LoginRequiredMixin, UserIsOwnerOrAdminMixin, UpdateView):
    model = CustomUser
    template_name = 'accounts/profile_update.html'

    def get_form_class(self):
        # ログインユーザーのロールに応じてフォームを切り替える
        if self.request.user.is_admin:
            return CustomUserChangeForm 
        else:
            return UserSelfUpdateForm
    
    def get_success_url(self):
        return reverse('accounts:profile_detail', kwargs={'pk': self.object.pk})

class CustomUserDeleteView(AdminOnlyMixin, DeleteView):
    model = CustomUser
    template_name = 'accounts/profile_delete.html'
    success_url = reverse_lazy('accounts:profile_list')

# パスワード変更処理
class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:password_change_done')

class CustomPasswordChangeDoneView(LoginRequiredMixin, PasswordChangeDoneView):
    template_name = 'accounts/password_change_done.html'

