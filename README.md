<p align="center"><img src="img/airfield_logo.png" alt="Airfield" width="128"></p>

<h1 align="center">Airfield</h1>

Airfield is an open source tool for the DC/OS ecosystem that enables teams to easily collaborate with shared Zeppelin instances.

The application consists of a micro service written in Flask and a User Interface written in Vue. It was developed and is being maintained by [MaibornWolff](https://www.maibornwolff.de/).


## Deployment

### Requirements
* DC/OS 1.11 or later
* Marathon-LB
* A wildcard DNS entry pointing at the loadbalancer. Each zeppelin instance will be available using a random name as a subdomain of your wildcard domain. As an example we will be using `*.zeppelin.mycorp`.
* A Key-Value-Store to store the list of existing zeppelin instances. Currently supported are either [consul](https://www.consul.io/) or [etcd](https://coreos.com/etcd/). If you have neither installed we recommend our [consul package](https://github.com/MaibornWolff/dcos-consul).
* Enough available resources to run both Airfield and one Zeppelin instance (minimum: 3 cores, 10GB RAM).

Airfield requires access to the Marathon API to manage zeppelin instances.
If you are running DC/OS Enterprise you need to create a serviceaccount for airfield:
```bash
dcos security org service-accounts keypair private-key.pem public-key.pem
dcos security org service-accounts create -p public-key.pem -d "Airfield service account" airfield-principal
dcos security secrets create-sa-secret --strict private-key.pem airfield-principal airfield/account-secret
dcos security org groups add_user superusers airfield-principal
```

### Package / Universe
Airfield is available in the [DC/OS Universe](https://universe.dcos.io).

First create a file `options.json`.
For DC/OS EE clusters you need at least the following (change values to fit your cluster):
```json
{
  "service": {
    "marathon_lb_vhost": "airfield.mycorp",
    "service_account_secret": "airfield/account-secret"
  },
  "airfield": {
    "marathon_lb_base_host": ".zeppelin.mycorp",
    "consul_endpoint": "http://api.aconsul.l4lb.thisdcos.directory:8500/v1"
  }
}
```

For DC/OS Open Source you need at least the following (change values to fit your cluster):
```json
{
  "service": {
    "marathon_lb_vhost": "airfield.mycorp"
  },
  "airfield": {
    "marathon_lb_base_host": ".zeppelin.mycorp",
    "consul_endpoint": "http://api.aconsul.l4lb.thisdcos.directory:8500/v1",
    "dcos_base_url": "http://leader.mesos"
  }
}
```

The following config parameters are optional:
* `service.virtual_network_enabled` and `service.virtual_network_name` if you want to run airfield in a virtual network
* `airfield.etcd_endpoint` if you want to use etcd instead of consul
* `airfield.app_group` if you want airfield to put the zeppelin instances into a different marathon app group
* `airfield.config_base_key` if you want airfield to use a different key prefix for consul/etcd

Then you can install airfield using the following commands:

```bash
dcos package install airfield --options=options.json
```

Wait for it to finish installing, then access airfield via the vhost you provided (`airfield.mycorp` in the example).

### Standalone Marathon App
We provide a [marathon app definition](marathon-deployment.json) for easy deployment.

The following settings need to be specified (see `TODO`s in the app definition):
* Either `AIRFIELD_CONSUL_ENDPOINT`: HTTP v1-Endpoint of your consul instance (for example `http://consul.marathon.l4lb.thisdcos.directory:8500/v1`)
* or `AIRFIELD_ETCD_ENDPOINT`: `host:port` of your etcd instance (for example `etcd.marathon.l4lb.thisdcos.directory:2379`).
* If running DC/OS EE: `DCOS_SERVICE_ACCOUNT_CREDENTIAL`: authorize Marathon access with service account. Change if you used a different secret.
* If running DC/OS OpenSource: `DCOS_BASE_URL`. Set it to `http://leader.mesos`
* Label `HAPROXY_0_VHOST`: URL you want Airfield to be reachable under (for example `airfield.mycorp`).

There a number of optional settings for Airfield that you can set using environment variables (see the [config file](airfield-microservice/config.py) for a complete list):
* Airfield will put all zeppelin instances into the marathon app group `airfield-zeppelin` by default. Set `AIRFIELD_MARATHON_APP_GROUP` to override it. Set it to an empty string to make airfield deploy all instances on the root level.
* By default all metadata will be stored in etcd/consul using the prefix `airfield`. You can override it by setting `AIRFIELD_CONFIG_BASE_KEY`.

Once you have configured the desired settings, you can deploy the application with the DC/OS CLI:
```
dcos marathon app add marathon-deployment.json
```

### OpenID Connect
You can protect Airfield via OpenID Connect. The following steps will setup a keycloak OpenID Connect authentication provider and connect it to Airfield.
1. Install your favourite version of keycloak, e.g. by running the provided ``docker-compose-dev.yml``
2. Create a new realm (in this example: airfield)
3. Create a role, a user and add the user to the role (you have to set the user's password manually)
4. Register a new client, enable authorisation and set valid redirect URIs
5. Adapt the provided ``resources/keycloak_example.json`` with the values from Realm Settings - OpenID endpoint configuration and the created client
6. Encode the created json base64 with ``base64 -wc 0 file.json`` to provide `AIRFIELD_OIDC_SECRET_FILE` or set `AIRFIELD_OIDC_SECRET_FILE_PATH`
7. Run with ``AIRFIELD_OIDC_ACTIVATED=1`` and `AIRFIELD_OIDC_SECRET_FILE` or `AIRFIELD_OIDC_SECRET_FILE_PATH`

## Usage
Airfield has a simple user interface that allows to interact with existing Zeppelin instances or create new instances with custom options.
### Create new Zeppelin Instance
Click on the 'Add Instance' button in the main screen to reach the screen depicted below.

![Airfield New Instance Screen](img/airfield_new.png)

Simply select the desired instance type to load its default configuration. You can edit general settings, the spark configuration, the administrative setting and specify additional packages to be installed. You are also able to view the costs per hour for the instance.
### Interact with a running Zeppelin Instance
![Airfield Main Screen](img/airfield_base.png)

Airfield lists all existing and deleted instances on the main screen. Besides being able to start, stop, restart or delete existing instances, the proxy URL to the instance is also shown. Even though the instance will be
recreated during most of the operations, notes will persist thanks to automatic import/export through Airfield. 

## Further Development
### Development Environment with docker-compose
This [script](docker-compose-dev.yml) uses docker-compose to set up a local development environment with Consul and Keycloak (OIDC) pre-configured.
The default values for the environment variables have been configured to use these endpoints

You will still need a running DC/OS cluster to deploy your application for testing.
### Local Backend
You need python >= 3.6 and an installed and configured dcos-cli (airfield uses the cli to get your cluster URL and an authentication token).

```bash
# Start consul in Docker container
docker run -d --rm --name=dev-consul -e CONSUL_BIND_INTERFACE=lo --net=host consul

# build frontend (at least once)
cd frontend && npm i && npm run build && cd ..

# Optional: use virtualenv
virtualenv airfield --python=/usr/bin/python3
source airfield/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set flask app location and debug mode
export FLASK_APP=app
export FLASK_ENV=development

# Set additional environment variables - see config.py
# Run locally for development
export AIRFIELD_CONSUL_ENDPOINT=http://localhost:8500/v1/
python run.py 
```
The Application will start on port 5000.

### Local Frontend
Install the latest version of node.js.
```bash
cd frontend

# Install dependencies
npm install

# Run locally for development with mock server
npm run dev

# Build for production
npm run build

# Run ESLint on source files
npm run lint
```

## Roadmap
The current release contains all basic functionality to collaborate with shared Zeppelin instances. Below is a list of future additions that will probably be included in a future release. Of course we can't give any guarantees :-)

* Usability improvements (only show creatable instances, allow adding GPUs to the instance, etc.)
* Check available resources in the cluster before trying to start a notebook to avoid that instances get stuck in staging
* Allow integration with dynamically scaling the DC/OS cluster by providing an interface that can be implemented to interact with the scaling mechanism used by your team. 
* Support for managing JupyterLab instances
* Provide more information on who created what for whom and usage durations in order to give more transparency regarding infrastructure costs.
