# CFDDNS

CFDDNS is a systemd-daemonized Cloudflare DDNS service. It updates the A/AAAA records of domains with your current IP address.

## Installation

You can install this program using the provided Makefile. The `make` command needs to be executed with root permissions. Alternatively, you can install this program manually following the commands in the Makefile.

```shell
git clone https://github.com/k4yt3x/cfddns
cd cfddns
sudo make install
```

## Removal

You can also remove this program from the system using the Makefile.

```shell
sudo make uninstall
```

## Enabling DDNS for a Domain

Suppose the domains we want to sync is `test.example.com`.

### 1. Create a new config file for the domain you want to sync

Make sure that the config file has permission 600. This ensures that no users other than root can read the API token. You can create a config file for each of the domains you wish to sync:

```shell
sudo cp /etc/cfddns/template.yaml /etc/cfddns/test.example.com.yaml
sudo cp /etc/cfddns/template.yaml /etc/cfddns/test2.example.com.yaml
```

Alternatively, since the two domains are both subdomains under the same top-level domain (TLD) `example.com`, you can create one config file for the TLD. CFDDNS will try to match the exact config file first. If it cannot find a config with the exact domain name, it will try to find the TLD's config file.

```shell
sudo cp /etc/cfddns/template.yaml /etc/cfddns/example.com.yaml
```

### 2. Get a Cloudflare API token and add it into the config file

Use an editor to open the file `/etc/cfddns/example.com.yaml`, and edit this line:

```yaml
token: YOUR_TOKEN_HERE
```

### 3. Enable the systemd service for the domain

```shell
sudo systemctl enable --now cfddns@test.example.com
```

### 4. Verify that DDNS is working

```shell
dig +short test.example.com
```

## Disabling DDNS for a Domain

Use the command below to list all enabled domains.

```shell
systemctl list-units --type=service --state=running | grep cfddns
```

Disable the service for the domain you wish to disable.

```shell
sudo systemctl disable --now cfddns@test.example.com
```

## License

- [cloudflare/python-cloudflare](https://github.com/cloudflare/python-cloudflare): MIT
