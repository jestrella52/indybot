from .models import Season

def season_processor(request):
    seasons = Season.objects.order_by('-year')
    return { 'seasons':seasons }
