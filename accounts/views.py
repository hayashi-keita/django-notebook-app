from asyncio import QueueEmpty
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView, LoginView
from .models import CustomUser
from notebook.models import Grade
from .forms import CustomUserChangeForm, CustomUserCreationForm, CustomPasswordChangeForm, CustomAuthenticationForm, UserSelfUpdateForm
from .mixins import AdminOnlyMixin, TeacherAndAdminOnlyMixin, UserIsOwnerOrStaffMixin, UserIsOwnerOrAdminMixin
from django.db.models import Q
from django.db import DatabaseError
from django.core.exceptions import ObjectDoesNotExist

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
        queryset = CustomUser.objects.all().select_related('grade', 'classroom').order_by('pk')
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(username__icontains=q) | Q(full_name__icontains=q)
            )
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role=role)
        grade_pk_param = self.request.GET.get('grade')
        if grade_pk_param:
            try:
                grade_pk = int(grade_pk_param)
                queryset = queryset.filter(grade=grade_pk)
            except ValueError:
                pass

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            # フィルタリングオプションのために全学年データを取得
            context['grades'] = Grade.objects.all().order_by('pk')
        except (DatabaseError, ObjectDoesNotExist) as e:
            # データベース接続エラーやテーブルが見つからない場合、ログを出力し、クラッシュを防ぐ
            print(f"ERROR: Failed to fetch Grade objects for context. Check migrations and DB connection: {e}")
            context['grades'] = [] # 空のリストを渡し、テンプレートの{% for %}ループを安全に通過させる
        context['q'] = self.request.GET.get('q', '')
        context['role'] = self.request.GET.get('role', '')
        context['grade'] = self.request.GET.get('grade', '')
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

