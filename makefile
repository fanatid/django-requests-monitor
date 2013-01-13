build: js css

debug: js_debug css_debug

watch:
	node src/watch.js

js:
	node src/js/build.js

js_debug:
	node src/js/build.js --debug

css:
	scss --compass src/css/app.scss requests_monitor/static/requests_monitor/css/app.css

css_debug: css

clean:
	find ./requests_monitor -type f -name \*.pyc -delete
	rm -rf ./build ./dist ./django_requests_monitor.egg-info
	rm -rf ./test_proj/env.bak.tar

install: build
	python setup.py install

uninstall:
	pip uninstall django-requests-monitor
