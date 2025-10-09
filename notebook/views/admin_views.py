from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from accounts.mixins import AdminOnlyMixin
from ..models import Grade, Classroom
from ..forms import GradeForm, ClassroomForm

# 学年管理
class GradeListView(AdminOnlyMixin, ListView):
    model = Grade
    template_name = 'notebook/grade_list.html'

class GradeCreateView(AdminOnlyMixin, CreateView):
    model = Grade
    form_class = GradeForm
    template_name = 'notebook/admin_form.html'
    success_url = reverse_lazy('notebook:grade_list')

class GradeUpdateView(AdminOnlyMixin, UpdateView):
    model = Grade
    form_class = GradeForm
    template_name = 'notebook/admin_form.html'
    success_url = reverse_lazy('notebook:grade_list')

class GradeDeleteView(AdminOnlyMixin, DeleteView):
    model = Grade
    template_name = 'notebook/admin_delete.html'
    success_url = reverse_lazy('notebook:grade_list')

# クラス管理
class ClassroomListView(AdminOnlyMixin, ListView):
    model = Classroom
    template_name = 'notebook/classroom_list.html'

class ClassroomCreateView(AdminOnlyMixin, CreateView):
    model = Classroom
    form_class = ClassroomForm
    template_name = 'notebook/admin_form.html'
    success_url = reverse_lazy('notebook:classroom_list')

class ClassroomUpdateView(AdminOnlyMixin, UpdateView):
    model = Classroom
    form_class = ClassroomForm
    template_name = 'notebook/admin_form.html'
    success_url = reverse_lazy('notebook:classroom_list')

class ClassroomDeleteView(AdminOnlyMixin, DeleteView):
    model = Classroom
    template_name = 'notebook/admin_delete.html'
    success_url = reverse_lazy('notebook:classroom_list')
