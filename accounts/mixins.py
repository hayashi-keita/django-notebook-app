from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

#管理者専用MIXIN
class AdminOnlyMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)
        # 1. LoginRequiredMixinの処理を実行 (未ログインならログイン画面へ)
        if hasattr(result, 'status_code') and result.status_code:
            return result
        # 2. ログイン済みだが、管理者ロールではない場合
        if not request.user.is_admin:
            return redirect('notebook:index')
        return result

# ログインかつ生徒であるかをチェックする
class StudentAndAdminMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_student or self.request.user.is_admin

# 担任または管理者であるかをチェック
class TeacherAndAdminOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_teacher or self.request.user.is_admin

# 自分自身または管理者かをチェック
class UserIsOwnerOrAdminMixin(UserPassesTestMixin):   
    def test_func(self):
        # 1. アクセス先のユーザーIDをURLのPKから取得
        user_pk_in_url = self.kwargs.get('pk')       
        # 2. ログインユーザー本人のID
        logged_in_user_pk = self.request.user.pk
        # 3. どちらの条件を満たすかチェック
        is_owner = logged_in_user_pk == user_pk_in_url
        is_admin = self.request.user.is_admin     
        # 💡 オーナー自身 または 管理者であれば True を返してアクセスを許可
        return is_owner or is_admin

# 自分自身、または管理者/先生のみが他人の詳細を見られ
class UserIsOwnerOrStaffMixin(UserPassesTestMixin):
    def test_func(self):
        # ログインチェック
        if not self.request.user.is_authenticated:
            raise PermissionDenied
        # アクセス先のユーザーIDをURLのPKから取得
        user_pk_in_url = self.kwargs.get('pk')
        # チェック条件
        is_owner = self.request.user.pk == user_pk_in_url
        is_staff = self.request.user.is_teacher or self.request.user.is_admin
        return is_owner or is_staff

