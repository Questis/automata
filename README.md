# Automata

Automata is a user management script that uses GitLab as a source for
user information written in Python 3.  Automata can grab the users associated with a specific
GitLab group and create user accounts on a Linux/UNIX server based on those
users

Automata generates a custom `/etc/sudoers.d` access file to give permissions
to each users as well as populate the user's `authorized_keys` file with the
keys associated with that user's GitLab account.

Access to GitLab requires a token that has API access.

## Configuration

All configuration options are contained within the `automata.yaml` file.

- `group`: The user group on the Linux/UNIX server to associated each account
with.  This is used to track which users should and should not fall under the
control of Automata
- `server`: All GitLab-related configuration options are contained within this group.
  - `api_address`: The full FQDN address of the API access point.
  - `api_token`: The GitLab token used to access the API.  This token must have
  permission to use the API.
  - `group`: The GitLab group that holds the required users.
- `logging`: Logging options for Automata
  - `log_level`: The logging levels available are `debug`, `info`, and `warn`.
  - `log_path`: The location of the Automata log file.  This file will be
  created on Automata's first run.
  - `log_format`: The format to use when logging.  This script uses Python's
  `logging` module, and this format should mirror what that module would use.
  - `sudoers_file`: This is the name of the `sudoers` configuration file to 
  use inside of `/etc/sudoers.d`.
  
```yaml
group: automated
server:
  api_address: "https://your.gitlab.server/api/v4"
  api_token: "xxxxxxxxxxxxxxxxxxxx"
  group: admins
logging:
  log_level: debug
  log_path: /var/log/automata.log
  log_format: '%(asctime)s [%(levelname)s] %(message)s'
sudoers_file: automated-users
```

## Installation

The `automata.yaml.example` file holds a good example to get going with configuring `automata`.  Also, there is an
`automata.yaml.ansible` file that already has variable placeholders inserted to make deploying with Ansible much easier.
Make sure that you save your configuration file as `automata.yaml`

Copy the files into a directory of your choice.  We'll use `/opt/automata` as an example.

Next, ensure that you can create Python virtual environments.  While you _could_ just install the packages listed in the
`requirements.txt` file, I recommend creating a virtual environment for Python and installing the packages into that
directory.  This will keep things nice and tidy.  The example below walks through setting up the Python virtual on
Ubuntu/Debian.

```console
$ sudo apt-get install python3-venv -y
$ cd /opt/automata
$ pyvenv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

Once everything is copied, edit the `ansible.yaml.example` file with your configuration information.  After this, the
only thing that really needs to be done is to setup a _cron_ job under `root` to kick off the script every 10 minutes or so.

```console
*/10 * * * * /opt/automata/venv/bin/python /opt/automata/automata.py
```

Now, all that's needed is to run the script on the server to get those sweet, sweet user accounts created.

## Things of Note
- Users with periods in their names (e.g. `john.doe`) will have the `.` replaced with an underscore (result: `john_doe`).
- Since none of the users have actual passwords, the `sudoers` file will contain a `NOPASSWD` entry for each.
- Each user gets a line in the `sudoers` configuration file specified above.

## Exit Codes

There are some established exit codes:

- `10`: Unable to connect to the GitLab server.
- `11`: This exit code is either a revoked or expired API token.
- `12`: This usually is a bad API token.
- `13`: Unknown error, look into the logs for more information.
