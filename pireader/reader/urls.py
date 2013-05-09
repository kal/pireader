from django.conf.urls import patterns, url
import views

urlpatterns = patterns(
    '',
    url(r'^$', views.index, name='index'),
    url(r'^import$', views.import_subscription, name='import'),
)
