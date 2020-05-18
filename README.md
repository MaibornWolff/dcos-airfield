<p align="center"><img src="img/airfield_logo.png" alt="Airfield" width="128"></p>

<h1 align="center">Airfield</h1>

Airfield is an open source tool for the DC/OS ecosystem that enables teams to easily collaborate with shared Zeppelin instances.

The application consists of a micro service written in Flask and a User Interface written in Vue. It was developed and is being maintained by [MaibornWolff](https://www.maibornwolff.de/).

## Deployment

### Requirements

* DC/OS 1.11 or later.
* [Marathon-LB](https://github.com/mesosphere/marathon-lb/) or [Edge-LB](https://docs.mesosphere.com/services/edge-lb/) to expose airfield under a subdomain (in this documentation `airfield.mycorp` is used as example).
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
    "consul_endpoint": "http://api.aconsul.l4lb.thisdcos.directory:8500/v1"
  }
}
```

If you use Edge-LB skip `service.marathon_lb_vhost` and instead add the following definition to your pool to expose airfield:

```yaml
...
haproxy:
  frontends:
    - bindPort: 80
      protocol: HTTP
      linkBackend:
        map:
          - hostEq: airfield.mycorp
            backend: airfield
  backends:
    - name: airfield
      protocol: HTTP
      services:
        - marathon:
            serviceID: "/airfield"
          endpoint:
            port: 5000
```

For DC/OS Open Source you need at least the following (change values to fit your cluster):

```json
{
  "service": {
    "marathon_lb_vhost": "airfield.mycorp"
  },
  "airfield": {
    "consul_endpoint": "http://api.aconsul.l4lb.thisdcos.directory:8500/v1",
    "dcos_base_url": "http://leader.mesos"
  }
}
```

Additionally there are a number of other parameters to configure airfield (for a complete list see the package options in [universe/options.json](universe/options.json) or by running `dcos package describe --config airfield`):

* `service.virtual_network_enabled` and `service.virtual_network_name` if you want to run the airfield app in a virtual network (recommended)
* `airfield.etcd_endpoint` if you want to use etcd instead of consul
* `airfield.app_group` if you want airfield to put the zeppelin instances into a different marathon app group
* `airfield.config_base_key` if you want airfield to use a different key prefix for consul/etcd
* `airfield.hdfs_config`: URL to download hdfs-site.xml and core-site.xml from to configure HDFS access. Will be passed to zeppelin instances. For a default DC/OS HDFS installation this is `http://api.hdfs.marathon.l4lb.thisdcos.directory/v1/endpoints`

Then you can install airfield using the following commands:

```bash
dcos package install airfield --options=options.json
```

Wait for it to finish installing, then access airfield via the vhost you provided (`airfield.mycorp` in the example).

### OpenID Connect

You can protect Airfield via OpenID Connect. For this you need keycloak or another openid-connect comptaible authentication system.

To configure airfield add a new client to your auth system and then create a configuration file (the example is for keycloak) with the following content:

```json
{
  "web": {
    "client_id": "airfield",
    "client_secret": "<client-secret>",
    "auth_uri": "https://keycloak.mycorp/auth/realms/master/protocol/openid-connect/auth",
    "redirect_uris": [
      "http://airfield.mycorp/oidc_callback"
    ],
    "token_uri": "https://keycloak.mycorp/auth/realms/master/protocol/openid-connect/token",
    "token_introspection_uri": "https://keycloak.mycorp/auth/realms/master/protocol/openid-connect/tokeninfo",
    "issuer": "https://keycloak.mycorp/auth/realms/master"
  }
}
```

Then base64-encode the file (e.g. by running ``base64 -wc 0 file.json``) and set the config option `airfield.oidc_config_base64` with its value.

### Marathon Groups

If you run DC/OS 2.0 or newer you can take advantage of the new quota management for marathon apps and have airfield deploy instances for different teams into different marathon groups to restrict their resource usage.
To do this create a json key-value-mapping of team names to marathon groups:

```json
{
  "group1": "airfield-group1",
  "group2": "airfield-group2"
}
```

Then base64-encode it and set the config option `airfield.dcos_groups_mapping_base64` with its value. During creation of an instance a user can select which group to deploy the instance in. Allowed groups for a user are taken from the openid connect system (so make sure the group names match). As such to use this feature you need to secure airfield with OpenID Connect (see above). For all instances launched in a group the `airfield.app_group` setting will be ignored.

### Cost tracking

Airfield includes a (as of yet rudimentary) cost tracking feature to show how much an instance costs. To enable this feature add the following options to your `options.json`:

```json
{
  "airfield": {
    "cost_tracking": {
      "enabled": true,
      "currency": "EURO",
      "cost_gb_per_minute": 0.01,
      "cost_core_per_minute": 0.05
    }
  }
}
```

For any created instance airfield will track how long the instance is/was running and calculate the cost total based on runtime minutes. The following rules apply:

* Instances only accure costs as long as they are running (stopped instances are free)
* Restarting an instance will not pause costs
* Reconfiguring an instance (e.g. changing the resources) will accure costs based on the new resources from the moment the reconfiguration is initiated
* The total resources on an instance are defined by the resources for the zeppelin instance itsself and the resources configured for spark executors (`Executor cores`, `Max cores` and `Executor RAM`)
* Airfield only tracks configured/allocated resources and not actual resource usage. So if you have configured spark executor resources for your instance but do not launch a spark job you will still be billed for the resources you could theoretically use.
* If an instance can not be successfully deployed due to not enough free resources the instance will still be billed until you stop the deployment.

The current total tost of an instance can be viewed in the instance details in airfield.

At the moment there is not yet a reporting system to get an overview of costs.

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
* Cost reporting
