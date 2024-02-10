# Setup
First, install dependencies to a Linux-based server (Debian is my preference, but should work on deriatives like Ubuntu, also):
```bash
apt install python3-bottle python3-yaml python3-paste nginx
```
  - Bottle is the web framework used to covert the backend script into a website
  - YAML is used to build external config, so the API stuff isn't hardcoded into the codebase
  - Paste is the server used by Bottle

Preliminary steps:

- Create an **administrator** user in the Unifi controller (without admin, you will get a Not Allowed response when trying to reboot an access point)

- Create a config file: `unificonfig.yml` and populate it with your details, alongside the codebase root - see [configuration](config.md) for explanation of these values:
```yaml
unifi:
    server: unifi.example.com
    port: 8443
    site: default
    api_user: apiuser
    api_pw: apipw
mail:
    server: mail.example.com
    port: 25
    sender_name: "John Smith"
    sender: support@example.com
    sender_pw: mailpw
    domain: "@example.com"
zendesk:
    user: you@example.com/token
    token: aBcDejFlkj46FFFJKLj455645df4df
    domain: example.zendesk.com
    assignee: 123456
debug: 0
site_admin: Angela
dev_hostname: devbox
email_subject: "Wifi Issue Follow-Up "
```


- If your web directory doesn't exist yet, create it:

```bash
mkdir -p /var/www
```

- Create a service for the application
```bash
pico /etc/systemd/system/helpdeskwifi.service
```

  - Populate with the following
    ```bash
    [Unit]
    Description=Helpdesk Wifi Dashboard
    After=network.target

    [Service]
    User=netbox
    ExecStart=/var/www/helpdeskwifi/unifi.py
    WorkingDirectory=/var/www/helpdeskwifi/
    Restart=on-failure
    RemainAfterExit=yes

    [Install]
    WantedBy=multi-user.target
    ```

- Test it
  ```bash
  service helpdeskwifi start
  ```

- Create a startup service (after server reboot, it will be auto-started):
```bash
systemctl enable helpdeskwifi
```

### How does the Python server work?
Note the following from the systemd unit file:
```bash
ExecStart=/var/www/helpdeskwifi/unifi.py
```
Open that file:
```bash
pico /var/www/helpdeskwifi/unifi.py
```

This is what speaks to nginx:
```python
run(server='paste', host='localhost', port=8000, debug=True)
```
If 8000 is already in use, just choose an unused port.

To see what ports are in use, run:
```bash
netstat -tunlp
```

To change from dev to prod, change:
```python
run(server='paste', host='localhost', port=8000, debug=True)
```

to:
```python
run(server='paste', host='localhost', port=8000, debug=False)
```

## On an existing Nginx-based system - Virtualhost Setup
Install Nginx (if not already installed)
```bash
apt install nginx
```

Virtualhost config for Nginx lives in `/etc/nginx`
Copy a pre-configured virtualhost, to save time

*(All of) the following steps are technically not required with Nginx (in this manner), but to keep similarity between Nginx and Apache systems, I keep the sites-available/sites-enabled setup.*

- **Port 80/non-SSL (direct URL types)**
  ```bash
  cp /etc/nginx/sites-available/helpdeskwifi /etc/nginx/sites-available/helpdeskwifi
  ```

- Symlink it to sites-enabled (this is the only step you'd have to do if you didn't care about Apache synchronicity) -- to break Apache-like behavior, bypass *sites-available* & use *sites-enabled*, only.
  ```bash
  ln -s /etc/nginx/sites-available/helpdeskwifi /etc/nginx/sites-enabled/helpdeskwifi
  ```

  - Contents of *helpdeskwifi*:
    ```bash
    server {
        listen 80;

        server_name helpdeskwifi.example.com;
        client_max_body_size 25m;

        location / {
            return 301 https://helpdeskwifi.example.com/;
        }
    }
    ```

- **Port 443/SSL (destination)**
  ```bash
  cp /etc/nginx/sites-available/helpdeskwifi /etc/nginx/sites-available/helpdeskwifi-ssl
  ```
- Symlink it to sites-enabled
  ```bash
  ln -s /etc/nginx/sites-available/helpdeskwifi /etc/nginx/sites-enabled/helpdeskwifi-ssl
  ```

  - Be sure to specify the path to your SSL/TLS certificates:
  - Contents of *helpdeskwifi-ssl* (note the proxy_pass field):
    ```bash
    server {
        listen 443 ssl;
        server_name helpdeskwifi.example.com;
        root /var/www/helpdeskwifi/;
        index unifi.py;
        ssl_certificate /path/to/your/certs/cert.pem;
        ssl_certificate_key /path/to/your/certs/key.pem;
        client_max_body_size 25m;

        location / {
            # whitelisted ips - add the helpdesk ip(s) here
            # failure to do so means nobody can access it, unless it's hosted on the machine it 
            # would be accessed from
            allow 127.0.0.1;
            deny all;
            root /var/www/helpdeskwifi/;
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header X-Forwarded-Host $server_name;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-Proto $scheme;
            add_header P3P 'CP="ALL DSP COR PSAa PSDa OUR NOR ONL UNI COM NAV"';
        }
    }
    ```

## Optional Multiple Push Destinations
Useful when you want to tweak & configure stuff on your local dev machine and only push it to your live site after it's to your liking.

If you don't already have a keypair setup from your dev box, you'll need your pubkey on the destination server.
[Github docs](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys#deploy-keys) explain how to do this, but it is not necessary to create a deployment key if your dev box already has the pubkey you shared with Github for pushing to repos.

1. Clone the repo locally (if it's already remote)
2. On the remote server, install git (if it's not already installed)
3.. On the **remote** server, run `git init` in `/var/www/gitdestination` and add to `.git/config`:
  ```bash
  [receive]
          denyCurrentBranch = updateInstead
  ```
4. In the **local dev box**, open `.git/config` inside your newly-cloned directory
5. Under **[remote "origin"]** you'll see the repo you just cloned, under `url =`
6. Add a new line beneath `url`, like so:
  ```bash
  pushurl = ssh://user@example.com:22/var/www/gitdestination
  pushurl = git@github.com:example.com/helpdeskwifi.git
  ```
7. Add a post-update hook on the **remote** server:
Create `.git/hooks/post-update` in `/var/www/gitdestination` with the following:
```bash
!/bin/sh

sudo service helpdeskwifi restart

```

8. Grant your standard user sudo permissions to restart the server:
```bash
visudo
```
  - Beneath:

    ```bash
    # User privilege specification
    root    ALL=(ALL:ALL) ALL
    ```

  - Add:

  ```bash
  youruser  ALL=(ALL) NOPASSWD: /usr/sbin/service helpdeskwifi restart
  ```

In order for your standard user's sudo permission to activate, your session may need to log out and log back in. 
