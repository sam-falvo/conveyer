 all: setup link run
 .PHONY: all

setup:
	apt-get update
	apt-get install pip
	pip install --upgrade pip
	apt-get uninstall pip
	pip install --upgrade virtualenv
	git clone git@github.com/sam-falvo/conveyer
	cd conveyer
	virtualenv .ve
	. .ve/bin/activate
	pip install -e .

link:
	export RMA=/usr/lib/rackspace-monitoring-agent/plugins
	cp plugins/conveyer-plugin.py $RMA
	chown --reference=$RMA $RMA/conveyer-plugin.py
	cp plugins/conveyer-plugin.json /etc
	chown --reference=$RMA /etc/conveyer-plugin.json

run:
	python conveyer/conveyer.py

