from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^circuit/list/$', views.circuit_list, name='circuit_list'),
    url(r'^circuit/create/$', views.circuit_create, name='circuit_create'),
    url(r'^circuit/(?P<circuit_id>[0-9]+)/edit/$', views.circuit_edit, name='circuit_edit'),
    url(r'^circuit/(?P<circuit_id>[0-9]+)/delete/$', views.circuit_delete, name='circuit_delete'),

    url(r'^country/list/$', views.country_list, name='country_list'),
    url(r'^country/create/$', views.country_create, name='country_create'),
    url(r'^country/(?P<country_id>[0-9]+)/edit/$', views.country_edit, name='country_edit'),
    url(r'^country/(?P<country_id>[0-9]+)/delete/$', views.country_delete, name='country_delete'),

    url(r'^driver/list/$', views.driver_list, name='driver_list'),
    url(r'^driver/list/active/$', views.driver_list_active, name='driver_list_active'),
    url(r'^driver/list/inactive/$', views.driver_list_inactive, name='driver_list_inactive'),
    url(r'^driver/create/$', views.driver_create, name='driver_create'),
    url(r'^driver/(?P<driver_id>[0-9]+)/edit/$', views.driver_edit, name='driver_edit'),
    url(r'^driver/(?P<driver_id>[0-9]+)/delete/$', views.driver_delete, name='driver_delete'),

    url(r'^liveries/regenerate/$', views.liveries_regenerate, name='liveries_regenerate'),
    url(r'^liveries/show/$', views.liveries_show, name='liveries_show'),
    url(r'^liveries/upload/$', views.liveries_upload, name='liveries_upload'),

    url(r'^race/list/$', views.race_list, name='race_list'),
    url(r'^race/list/season/(?P<season>[0-9]+)$', views.race_list, name='race_list'),
    url(r'^race/create/$', views.race_create, name='race_create'),
    url(r'^race/(?P<race_id>[0-9]+)/edit/$', views.race_edit, name='race_edit'),
    url(r'^race/(?P<race_id>[0-9]+)/delete/$', views.race_delete, name='race_delete'),

    url(r'^redditaccount/list/$', views.redditAccount_list, name='redditAccount_list'),
    url(r'^redditaccount/create/$', views.redditAccount_create, name='redditAccount_create'),
    url(r'^redditaccount/(?P<redditaccount_id>[0-9]+)/edit/$', views.redditAccount_edit, name='redditAccount_edit'),
    url(r'^redditaccount/(?P<redditaccount_id>[0-9]+)/delete/$', views.redditAccount_delete, name='redditAccount_delete'),

    url(r'^results/edit/(?P<race_id>[0-9]+)/(?P<resulttype_id>[0-9]+)/$', views.results_edit, name='resultsEdit'),
    url(r'^results/update/(?P<race_id>[0-9]+)/(?P<resulttype_id>[0-9]+)/$', views.results_update, name='results_update'),

    url(r'^resulttype/list/$', views.resultType_list, name='resultType_list'),

    url(r'^season/list/$', views.season_list, name='season_list'),
    url(r'^season/create/$', views.season_create, name='season_create'),
    url(r'^season/(?P<season_id>[0-9]+)/edit/$', views.season_edit, name='season_edit'),
    url(r'^season/(?P<season_id>[0-9]+)/delete/$', views.season_delete, name='season_delete'),

    url(r'^start/list/$', views.start_list, name='start_list'),

    url(r'^type/list/$', views.type_list, name='type_list'),

    url(r'^post/list/$', views.post_list, name='post_list'),
    url(r'^post/list/pending/$', views.post_list_pending, name='post_list_pending'),
    url(r'^post/create/$', views.post_create, name='post_create'),
    url(r'^post/(?P<post_id>[0-9]+)/edit/$', views.post_edit, name='post_edit'),
    url(r'^post/(?P<post_id>[0-9]+)/delete/$', views.post_delete, name='post_delete'),

    url(r'^login$', views.login, name='login'),
    url(r'^logout$', 'django.contrib.auth.views.logout', {'template_name': 'logout.html'}),

    url(r'^password_change/$', 'django.contrib.auth.views.password_change', {'template_name': 'passwordChange.html'}),
    url(r'^password_change_done/$', 'django.contrib.auth.views.password_change_done', {'template_name': 'passwordChangeDone.html'}, name='password_change_done'),
]
