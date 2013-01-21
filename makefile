build:
	grunt

watch:
	grunt watch

clean:
	find ./requests_monitor -type f -name \*.pyc -delete
	rm -rf ./build ./dist ./django_requests_monitor.egg-info
	rm -rf ./test_proj/env.bak.tar

install: build
	python setup.py install

uninstall:
	pip uninstall django-requests-monitor
