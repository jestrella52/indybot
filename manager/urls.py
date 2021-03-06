from django.conf import settings
from django.conf.urls import include, url
from django.contrib import auth
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^caution/(?P<caution_id>[0-9]+)/race/(?P<race_id>[0-9]+)/delete$', views.caution_delete, name='caution_delete'),
    url(r'^cautiondriver/(?P<cautiondriver_id>[0-9]+)/race/(?P<race_id>[0-9]+)/delete$', views.cautiondriver_delete, name='cautiondriver_delete'),

    url(r'^channel/list/$', views.channel_list, name='channel_list'),
    url(r'^channel/create/$', views.channel_create, name='channel_create'),
    url(r'^channel/(?P<channel_id>[0-9]+)/edit/$', views.channel_edit, name='channel_edit'),
    url(r'^channel/(?P<channel_id>[0-9]+)/delete/$', views.channel_delete, name='channel_delete'),

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
    url(r'^driver/list/current/$', views.driver_list_current, name='driver_list_current'),
    url(r'^driver/list/inactive/$', views.driver_list_inactive, name='driver_list_inactive'),
    url(r'^driver/create/$', views.driver_create, name='driver_create'),
    url(r'^driver/list/shared/$', views.driver_list_shared, name='driver_list_shared'),

    url(r'^driver/(?P<driver_id>[0-9]+)/edit/$', views.driver_edit, name='driver_edit'),
    url(r'^driver/(?P<driver_id>[0-9]+)/delete/$', views.driver_delete, name='driver_delete'),
    url(r'^driver/(?P<driver_id>[0-9]+)/toggleActive/$', views.driver_toggleActive, name='driver_toggleActive'),

    url(r'^liveries/regenerate/$', views.liveries_regenerate, name='liveries_regenerate'),
    url(r'^liveries/show/$', views.liveries_show, name='liveries_show'),
    url(r'^liveries/upload/$', views.liveries_upload, name='liveries_upload'),

    url(r'^output/$', views.output, name='output'),

    url(r'^race/list/$', views.race_list, name='race_list'),
    url(r'^race/list/season/(?P<season>[0-9]+)$', views.race_list, name='race_list'),
    url(r'^race/(?P<pk>[0-9]+)/caution/edit/$', views.EditCautionsView.as_view(), name='caution_edit'),
    url(r'^race/(?P<race_id>[0-9]+)/session/edit/$', views.session_edit, name='session_edit'),
    url(r'^race/create/$', views.race_create, name='race_create'),
    url(r'^race/(?P<race_id>[0-9]+)/edit/$', views.race_edit, name='race_edit'),
    url(r'^race/(?P<race_id>[0-9]+)/delete/$', views.race_delete, name='race_delete'),
    url(r'^race/(?P<race_id>[0-9]+)/thread/$', views.race_thread, name='race_thread'),

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

    url(r'^sessiontype/list/$', views.sessiontype_list, name='sessiontype_list'),
    url(r'^sessiontype/create/$', views.sessiontype_create, name='sessiontype_create'),
    url(r'^sessiontype/(?P<sessiontype_id>[0-9]+)/edit/$', views.sessiontype_edit, name='sessiontype_edit'),
    url(r'^sessiontype/(?P<sessiontype_id>[0-9]+)/delete/$', views.sessiontype_delete, name='sessiontype_delete'),

    url(r'^sidebar/update/$', views.sidebar_update, name='sidebar_update'),

    url(r'^start/list/$', views.start_list, name='start_list'),

    url(r'^task/(?P<task_id>[0-9a-f\-]+)/status/', views.task, name='task'),

    url(r'^tasks/$', views.tasks, name='tasks'),
    url(r'^tasks/(?P<task_name>[A-Za-z]+)/$', views.tasks, name='tasks'),

    url(r'^tweet/list/$', views.tweet_list, name='tweet_list'),
    url(r'^tweet/create/$', views.tweet_create, name='tweet_create'),
    url(r'^tweet/(?P<tweet_id>[0-9]+)/edit/$', views.tweet_edit, name='tweet_edit'),
    url(r'^tweet/(?P<tweet_id>[0-9]+)/delete/$', views.tweet_delete, name='tweet_delete'),

    url(r'^type/list/$', views.type_list, name='type_list'),

    url(r'^post/list/$', views.post_list, name='post_list'),
    url(r'^post/list/pending/$', views.post_list_pending, name='post_list_pending'),
    url(r'^post/create/$', views.post_create, name='post_create'),
    url(r'^post/(?P<post_id>[0-9]+)/edit/$', views.post_edit, name='post_edit'),
    url(r'^post/(?P<post_id>[0-9]+)/delete/$', views.post_delete, name='post_delete'),

    url(r'^login$', views.login, name='login'),
    url(r'^logout$', auth_views.logout, {'template_name': 'logout.html'}),

    url(r'^password_change/$', auth_views.password_change, {'template_name': 'passwordChange.html'}),
    url(r'^password_change_done/$', auth_views.password_change_done, {'template_name': 'passwordChangeDone.html'}, name='password_change_done'),
]

if settings.INDYBOT_ENV == "DEVEL":
    import debug_toolbar
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
    urlpatterns += staticfiles_urlpatterns()
