help:
	@echo 'usage: (sudo) make install|uninstall'

install:
	pip3 install -U -r src/requirements.txt

	cp src/cfddns.py /usr/local/bin/cfddns
	cp src/cfddns@.service /etc/systemd/system/cfddns@.service
	mkdir -p /etc/cfddns
	cp src/template.yaml /etc/cfddns/template.yaml

	chown root: /usr/local/bin/cfddns /etc/systemd/system/cfddns@.service /etc/cfddns/template.yaml
	chmod 755 /usr/local/bin/cfddns
	chmod 644 /etc/systemd/system/cfddns@.service
	chmod 600 /etc/cfddns/template.yaml

	@echo 'CFDDNS installed'

uninstall:
	rm -rf /usr/local/bin/cfddns /etc/systemd/system/cfddns@.service /etc/cfddns
	@echo 'CFDDNS uninstalled'
