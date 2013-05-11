from django.conf.urls import patterns, url
import views

urlpatterns = patterns(
    '',
    url(r'^$', views.index, name='index'),
    url(r'^import$', views.import_subscription, name='import'),
    url(r'^subscriptions$', views.subscriptions),
    url(r'^subscriptions/(?P<feed_id>\d+)$', views.feed)
)