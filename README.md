<p align="center"><img src="img/airfield_logo.png" alt="Airfield" width="128"></p>

<h1 align="center">Airfield</h1>

Airfield is an open source tool for the DC/OS ecosystem that enables teams to easily collaborate with shared Zeppelin instances.

The application consists of a micro service written in Flask and a User Interface written in Vue. It was developed and is being maintained by [MaibornWolff](https://www.maibornwolff.de/).

* [Version](#version)
* [License](#license)
1. [Setup](#setup)
    * [Marathon and Marathon-LB](#marathon-and-marathon-lb)
    * [Consul](#consul)
    * [Prometheus](#prometheus)
    * [Optional Settings](#optional-settings)
2. [Deployment](#deployment)
3. [Usage](#usage)
    * [Create new Zeppelin Instance](#create-new-zeppelin-instance)
    * [Modify existing Zeppelin Instances](#modify-existing-zeppelin-instances)
    * [Use a running Zeppelin Instance](#use-a-running-zeppelin-instance)
4. [Further Development](#further-development)
    * [Development Environment with docker-compose](#development-environment-with-docker-compose)
    * [Local Backend](#local-backend)
    * [Local Frontend](#local-frontend)
5. [Roadmap](#roadmap)

#### Version
Airfield is currently under active development. Docker images based on the current master are available from [DockerHub](https://hub.docker.com/r/maibornwolff/airfield/).

#### License
Apache License Version 2.0

## Deployment
The following setup guide assumes you have a running DC/OS cluster with enough available resources to run both Airfield and some Zeppelin instances.

Airfield depends on a number of third party services that need to be running in your DC/OS environment:
* Marathon-LB is used to expose started zeppelin instances. You must have a wildcard DNS entry pointing at the loadbalancer. Each instance will be available using a random name as a subdomain of your wildcard domain (see `AIRFIELD_BASE_HOST` below).
* [Consul](https://www.consul.io/) is used to store the list of existing zeppelin instances (see `AIRFIELD_CONSUL_ENDPOINT` below). The base key is individually configurable, see the [config file](airfield-microservice/config.py) for details.


Airfield requires access to the Marathon API to manage zeppelin instances. You need to create a serviceaccount for it:
```
dcos security org service-accounts keypair private-key.pem public-key.pem
dcos security org service-accounts create -p public-key.pem -d "Airfield service account" airfield-principal
dcos security secrets create-sa-secret --strict private-key.pem airfield-principal airfield/account-secret
dcos security org groups add_user superusers airfield-principal
```

We provide a [marathon app definition](marathon-deployment.json) for easy deployment.

The following settings need to be specified (see `TODO`s in the app definition):
* `AIRFIELD_BASE_HOST`: Base DNS name to use for zeppelin instances (make sure its wildcard entry points towards your loadbalancer). Example: If you set it to `.zeppelin.mycorp` a zeppelin instance will be reachable via `<randomname>.zeppelin.mycorp`.
* `AIRFIELD_CONSUL_ENDPOINT`: HTTP URL of your consul instance (for example `http://consul.marathon.l4lb.thisdcos.directory:8500`).
* `DCOS_SERVICE_ACCOUNT_CREDENTIAL`: authorize Marathon access with service account. Change if you used a different secret.
* `HAPROXY_0_VHOST`: URL you want Airfield to be reachable under (for example `airfield.mycorp`).

There a number of optional settings for Airfield that you can set using environment variables, see the [config file](airfield-microservice/config.py) for details.

Once you have configured the desired settings, you can deploy the application with the DC/OS CLI:
```
dcos marathon app add marathon-deployment.json
```

## Usage
Airfield has a simple user interface that allows to interact with existing Zeppelin instances or create new instances with custom options.
### Create new Zeppelin Instance
Click on the 'Add Instance' button in the main screen to reach the screen depicted below.

![Airfield New Instance Screen](img/airfield_new.png)

Simply select the desired instance type to load its default configuration. You can edit general settings, the spark configuration and specify additional packages to be installed.
### Interact with a running Zeppelin Instance
![Airfield Main Screen](img/airfield_base.png)

Airfield lists all existing instances on the main screen. Besides being able to start, stop, restart or delete existing instances, the URL to the instance is also shown.

## Further Development
### Development Environment with docker-compose
This [script](docker-compose-dev.yml) uses docker-compose to set up a local development environment with Consul and Keycloak (OIDC) pre-configured.
The default values for the environment variables have been configured to use these endpoints

You will still need a running DC/OS cluster to deploy your application for testing.
### Local Backend
You need python >= 3.5 and an installed and configured dcos-cli (airfield uses the cli to get your cluster URL and an authentication token).

```bash
cd airfield-microservice

# Optional: use virtualenv
mkvirtualenv airfield --python=/usr/bin/python3

# Install dependencies
pip install -r requirements.txt

# Set flask app location and debug mode
export FLASK_APP=app
export FLASK_ENV=development

# Set additional environment variables - see config.py
# Run locally for development
flask run
```

### Local Frontend
Install the latest version of node.js.
```bash
cd airfield-frontend

# Install dependencies
npm i

# Run locally for development with mock server
npm run dev

# Run locally for development with backend server
npm run dev-server

# Build for production
npm run build

# Run ESLint on source files
npm run lint
```

## Roadmap
The current release contains all basic functionality to collaborate with shared Zeppelin instances. Below is a list of future additions that will be included in a next release.

1. Securing the application with OIDC
2. Usability improvements (only show creatable instances, allow adding GPUs to the instance, etc.)
3. Adding notebook templates to be created automatically on instance start
