from django.db.models import Count
from .models import Race, Season

def season_processor(request):
    seasons = Season.objects.order_by('-year')
    seasonGroups = Race.objects.values('season_id').annotate(seasonracecount = Count('season_id'))
    seasonRaceCount = {}
    for item in seasonGroups:
        seasonRaceCount[item['season_id']] = item['seasonracecount']

    for season in seasons:
        if season.id not in seasonRaceCount:
            seasonRaceCount[season.id] = 0

    return {
        'seasons':seasons,
        'seasonRaceCount':seasonRaceCount,
    }
