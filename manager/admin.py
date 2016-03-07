from django.contrib import admin

# Register your models here.
from .models import Country, Course, Driver, Race, Result, ResultType, Start, Type

# class QualResultInline(admin.TabularInline):
#     model = Result.races.through
#     extra = 21
#
# class RaceAdmin(admin.ModelAdmin):
#     inlines = [QualResultInline]
#
# class ResultAdmin(admin.ModelAdmin):
#     inlines = [QualResultInline]
#     exclude = ('races')

admin.site.register(Country)
admin.site.register(Course)
admin.site.register(Driver)
admin.site.register(Race)
admin.site.register(Result)
admin.site.register(ResultType)
admin.site.register(Start)
admin.site.register(Type)
