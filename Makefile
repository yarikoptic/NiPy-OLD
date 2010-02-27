# Automating common tasks for NIPY development

clean:
	find . -regex ".*\(\.pyc\|\.so\|~\|#\)" -exec rm -rf "{}" \;
	rm -rf build

dev:
	python setup.py build_ext --inplace
	./tools/mynipy

test:
	cd .. && python -c 'import nipy; nipy.test()'

build:
	python setup.py build

install:
	python setup.py install
