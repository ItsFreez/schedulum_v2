import datetime as dt

from django.apps import apps
from django.core.exceptions import ValidationError
from django.conf import settings

CURRENT_MONTH = settings.CURRENT_MONTH
CURRENT_YEAR = settings.CURRENT_YEAR
DATES = settings.VALIDATE_DATES
NOT_EXIST_WEEK_ERROR = ('Вы пытаетесь добавить расписание '
                        'на несуществующую неделю.')
INVALID_PAST_ERROR = 'Август и Июль неучебные месяцы.'


def correct_start(date):
    correct_month = dt.date(year=CURRENT_YEAR, month=CURRENT_MONTH, day=1)
    if date < correct_month:
        raise ValidationError('Прошедший месяц не доступен для выбора.')
    if (DATES['CURRENT_JULY'] < date < DATES['CURRENT_AUGUST']
            or DATES['NEXT_JULY'] < date < DATES['NEXT_AUGUST']):
        raise ValidationError(INVALID_PAST_ERROR)
    return date


def correct_end(date):
    if (DATES['CURRENT_START_JULY'] < date < DATES['CURRENT_END_AUGUST']
            or DATES['NEXT_START_JULY'] < date < DATES['NEXT_END_AUGUST']):
        raise ValidationError(INVALID_PAST_ERROR)
    return date


def validate_exist_week(date):
    model = apps.get_model(app_label='schedules', model_name='Week')
    obj = model.objects.filter(start__lte=date, end__gte=date).first()
    if obj is None:
        raise ValidationError(NOT_EXIST_WEEK_ERROR)
    return date
