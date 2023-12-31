import datetime

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.views.generic import (CreateView, DeleteView, ListView,
                                  TemplateView, UpdateView)
from django.urls import reverse_lazy

from schedules.forms import ScheduleCreationForm, ScheduleEditForm
from schedules.models import Month, Year, Week, Schedule, User

CURRENT_DAY = settings.CURRENT_DAY
NEXT_DAY = settings.NEXT_DAY


def csrf_failure(request, reason=''):
    """Кастомная ошибка 403."""
    return render(request, 'error_pages/403csrf.html', status=403)


def page_not_found(request, exception):
    """Кастомная ошибка 404."""
    return render(request, 'error_pages/404.html', status=404)


def server_error(request):
    """Кастомная ошибка 500."""
    return render(request, 'error_pages/500.html', status=500)


class ScheduleChangeMixin(LoginRequiredMixin):
    """Миксин для обновления и удаления объектов Schedule."""

    model = Schedule
    slug_url_kwarg = 'date'
    template_name = 'schedules/schedule_form.html'
    success_url = reverse_lazy('schedules:calendar')

    def dispatch(self, request, *args, **kwargs):
        """Получение объекта пользователя или ошибка."""
        self.user = get_object_or_404(User, username=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        """Получение объекта расписания по пользователю и дате."""
        if queryset is None:
            queryset = self.get_queryset()
        date_str = self.kwargs.get(self.slug_url_kwarg)
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        obj = get_object_or_404(Schedule, date=date, author=self.user)
        return obj


class IndexView(TemplateView):
    """View для стартовой страницы сервиса."""

    template_name = 'schedules/index.html'


class CalendarView(LoginRequiredMixin, ListView):
    """View для страницы календаря."""

    model = Month
    template_name = 'schedules/calendar.html'

    def get_queryset(self):
        """Получение объектов Year, Month, Week."""
        self.year_objects = Year.objects.all()[:2]
        self.week_objects = Week.objects.all()
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        """Передача объектов в template через словарь context."""
        context = super().get_context_data(**kwargs)
        context['years'] = self.year_objects
        context['weeks'] = self.week_objects
        return context


class DayListView(LoginRequiredMixin, ListView):
    """View для страницы расписания на неделю."""

    template_name = 'schedules/daylist.html'

    def dispatch(self, request, *args, **kwargs):
        """Получение объектов пользователя, Year, Month, Week или ошибка."""
        self.user = get_object_or_404(User, username=request.user)
        year = get_object_or_404(Year, year=kwargs['year'])
        month = get_object_or_404(Month, title=kwargs['month_titl'], year=year)
        week_title = kwargs['week_title']
        week_title = week_title.replace('%20', ' ')
        self.week = get_object_or_404(Week, title=week_title, month=month)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """
        Получение и передача объектов Schedule в template исходя из их
        номера дня недели, номера недели и пользователя.
        """
        schedules = []
        for number in range(7):
            date = self.week.start + datetime.timedelta(days=number)
            schedule = Schedule.objects.filter(
                date__week_day=date.weekday() + 2,
                author=self.user,
                week=self.week
            ).first()
            date_schedule_tuple = (date, schedule)
            schedules.append(date_schedule_tuple)
        return schedules


class ScheduleCreateView(LoginRequiredMixin, CreateView):
    """View для формы создания расписания."""

    model = Schedule
    form_class = ScheduleCreationForm
    template_name = 'schedules/schedule_form.html'
    success_url = reverse_lazy('schedules:calendar')

    def get_form_kwargs(self):
        """Передача объекта текущего пользователя в форму."""
        kwargs = super().get_form_kwargs()
        kwargs.update({'author': self.request.user})
        return kwargs


class ScheduleUpdateView(ScheduleChangeMixin, UpdateView):
    """View для формы редактирования расписания."""

    form_class = ScheduleEditForm


class ScheduleDeleteView(ScheduleChangeMixin, DeleteView):
    """View для удаления расписания."""

    pass


class ProfileView(LoginRequiredMixin, ListView):
    """View для профиля пользователя."""

    template_name = 'schedules/profile.html'

    def get_queryset(self):
        """
        1. Получение объекта пользователя или ошибка;
        2. Получение объектов Schedule на сегодняшнюю и завтрашнюю дату;
        3. Передача объектов в template.
        """
        self.user = get_object_or_404(User, username=self.request.user)
        schedules = []
        for day, title in ((CURRENT_DAY, 'Сегодня'), (NEXT_DAY, 'Завтра')):
            week = Week.objects.filter(
                start__lte=day,
                end__gte=day
            ).first()
            schedule = Schedule.objects.filter(
                date__week_day=day.weekday() + 2,
                author=self.user,
                week=week,
            ).first()
            schedule_date_tuple = (schedule, day, title)
            schedules.append(schedule_date_tuple)
        return schedules

    def get_context_data(self, **kwargs):
        """Передача объекта пользователя в template через словарь context."""
        context = super().get_context_data(**kwargs)
        context['profile'] = self.user
        return context
