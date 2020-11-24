# Forge, the Satellite orchestration tool

Forge is a tool based on [nailgun](https://github.com/SatelliteQE/nailgun). It builds a satellite server from a plain RHEL7 image up to repositories, content-views, activationkeys based on a single config-file, with idempotency.

It was tested and developped on RHEL7.8 with Satellite 6.7.

It was written to generate content-views with various Zstream for the OpenStack products but can be adapted for any needs.

# Installation

- Copy `env.example` file and edit according to your needs.
- Either spin a VM by using the cloud-init script `openstack-tools/satellite-user-data.txt` or just execute each commands manually.
- Validate the content of `./openstack-tools/server_create.sh` and adapt as well.
- Execute the server create
```
$ source openstack-tools/cee-shared-space-openrc.sh
$ ./openstack-tools/server_create.sh
```
- This will spin an instance. It might take a good amount of time to fully provision it. After the final configuration, the instance will reboot, fully updated.
- SSH into the instance and run the unattended installation
```
root@satellite ~/forge/ # ./forger.py install
```
- This will also take a while to install. Once it's completed, you can run the rest from your laptop.
- Validate the content of `./sat.cfg` and adapt.
- Initialize the satellite with some default objects and resources
```
me@localhost ~/forge $ ./forger.py make init
```
- Now let's enable and synchronise the `repository-sets`
```
me@localhost ~/forge $ ./forger.py make repo-sets -s
```
- Let's generate container `products` and sync the container `repositories`
```
me@localhost ~/forge $ ./forger.py make container-repos -s
```
- Time to generate the `content-views`
```
me@localhost ~/forge $ ./forger.py make content-views
```
- We're almost done here, let's generate the `activation-keys`
```
me@localhost ~/forge $ ./forger.py make activation-keys
```
- Finally, we can generate the container-image-prepare if required:
```
me@localhost ~/forge $ ./forger.py make container-prepare -r OSP16.1 -z z2 -u container_puller -p q1w2e3
```

# Some help

The `openstack-tools` folder contains some tools to spin a VM on the [coporate openstack deployment](https://control.stack.rdu2.cee.redhat.com/)

The `install` has to be executed on the satellite host itself because it runs the package installation, `satellite-installer` and initial configuration. We also need `python-3.8` on the satellite host for the installation process because of the way we run the `subprocess`.
```
yum install -y rh-python38-python.x86_64 rh-python38-python-libs.x86_64 rh-python38-python-pip.noarch rh-python38-python-psutil.x86_64 rh-python38-python-requests.noarch
scl enable rh-python38 "python3.8 -m virtualenv .python3"
source .python3/bin/activate
pip3 install -r requirements.txt
```

The file `sat.cfg` contains the configuration and should be pretty much self-explanatory.

There's also some scripted aliases to pull out and format interesting data like the sync and tasks status.

```
$ forger.py --help
Usage: forger.py [OPTIONS] COMMAND [ARGS]...

Options:
  -v, --verbose                Will print debug messages.
  -c, --config-file TEXT       Configuration file  [default: sat.cfg]
  -s, --satellite-server TEXT  Satellite server name to work on
  --help                       Show this message and exit.

Commands:
  check    Performs various validations and verification
  install  Installs satellite on the local system
  make     Generates and creates various components

$ forger.py make --help
Usage: forger.py make [OPTIONS] COMMAND [ARGS]...

  Generates and creates various components

Options:
  --help  Show this message and exit.

Commands:
  activation-keys    Creates the Activation Keys
  container-prepare  Generates the container-prepare template
  container-repos    Generates the products and repositories based on the...
  content-views      Generates the content-views based on the configuration
  init               Initializes the satellite server with some sync plans,...
  repo-sets          Enables the required repository-sets


$ forger.py check --help
Usage: forger.py check [OPTIONS] COMMAND [ARGS]...

  Performs various validations and verification

Options:
  --help  Show this message and exit.

Commands:
  content-views  Searches the Content Views
  repos          Searches the repository-sets
  sync           Returns the sync status for all repos
  task           Task manipulation
```

# More tricks
* Some resources have additionnal options like `make content-views` and `make activation-keys` support passing some filters. It's then possible to generate or update the `activation-keys` for a whole OpenStack release, or even a Zrelease.
```
me@localhost $ ./forger.py make activation-keys --help
Usage: forger.py make activation-keys [OPTIONS]

  Creates the Activation Keys

Options:
  -z, --z-releases [GA|latest|z1|z2|z3|z4|z5|z6|z7|z8|z9|z10|z11|z12|z13|z14|z15|z16|z17|z18|z19]
                                  OpenStack Z Releases
  -r, --stack-releases [OSP10|OSP13|OSP16.1]
                                  OpenStack Releases
  --help                          Show this message and exit.
```

* If something goes wrong, it's always possible to enable debug log with `-v` switch like this:
```
me@localhost $ ./forger.py -v make init
```
* `forge` is idempotent, it will create or update.

# TODO
* Docstring everything
* User creation process
* Cleanup a bunch of things like logging.
* Reformat multiline string with better indentation
* More progressbars, less logging.
* Log debug to file by default
* loading manifest using nailgun
