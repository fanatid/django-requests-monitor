from django.conf.urls import patterns, url


urlpatterns = patterns('',
	url(r'^$', 'test_proj.views.index'),
)
