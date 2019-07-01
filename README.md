# Automata

Automata is a user management script that uses GitLab as a source for
user information.  Automata can grab the users associated with a specific
GitLab group and create user accounts on a Linux/UNIX server based on those
users

Automata generates a custom `/etc/sudoers.d` access file to give permissions
to each users as well as populate the user's `authorized_keys` file with the
keys associated with that user's GitLab account.

Access to GitLab requires a token that has API access.

## Configuration

All configuration options are contained within the `automata.yaml` file.


```yaml
# vim:ts=2:sts=2:sw=2:et
---
gitlab:
  server:
    api_address: "https://gitlab.myserver.com/api/v4"
    api_token: "abcdefg1234567"
    sudoers_file: "/etc/sudoers.d/automata"
    home_dir_path: '/home'
  groups:
    open-source:
      linux_group: open_source
      sudoers_line: 'ALL=(ALL) NOPASSWD: ALL'
      other_groups:
        - docker
    another-group:
      linux_group: another_group
      sudoers_line: 'ALL=(ALL) NOPASSWD: ALL'
logging:
  log_level: debug
  log_path: /var/log/automata.log
  log_format: '%(asctime)s [%(levelname)s] %(message)s'
```

- `gitlab`: All Gitlab configuration options fall under this key.  This includes server connectivity, group mappings, and `sudoers` settings
  - `server`: Gitlab server settings
    - `api_address`: The full address to the API endpoint. This should be something like `https://gitlab.myserver.com/api/v4`
    - `api_token`: The token to access the Gitlab API.  This is optional as you can also pass `automata` the access token via the `GL_API_TOKEN` environment variable.
    - `sudoers_file`: The location of the sudoers file to create.
    - `home_dir_path`: The base path for all user home directories created by `automata` 
  - `groups`: All user/group mapping and sudoers configuration information goes under this key.  Each key under this should be the Gitlab group name to use for authentication.  In the example above, the group being used is the `open-source` group on the Gitlab server.  You can specify more than one group, users in the top-most groups will take precedence over the groups defined below them.
    - `linux_group`: The group on the target server to use.  This group will be created if it doesn't exist, and any user in the active state in the Gitlab `open-source` group will be created as part of that group.
    - `sudoers_line`: The settings for the users created by `automata`.  The line will be prepended with the proper group information.
    - `groups`: Additional groups to associate with the users being created by automata.
- `logging`: Logging options for Automata
  - `log_level`: The logging levels available are `debug`, `info`, and `warn`.
  - `log_path`: The location of the Automata log file.  This file will be
  created on Automata's first run.
  - `log_format`: The format to use when logging.  This script uses Python's
  `logging` module, and this format should mirror what that module would use.

## Installation

You will need to install Python 3 for this to work.  It will not work under Python 2 without some major changes.

1. Copy everything to a directory like `/opt/automata`.
2. Navigate to `/opt/automata` and create the Python virtual environment:

   ```console
   $ cd /opt/automata
   $ python3 -m venv venv
   ```

3. Install all of the requirements in the `requirements.txt` file

   ```console
   $ source venv/bin/activate
   $ pip install -r requirements.txt
   ```

4. Copy the `automata.conf.example.yaml` file to `automata.conf` and edit the `automata.conf` file with the appropriate settings.

5. Run the `automata` script, and let it do it's magic.

   ```console
   $ python automata.py
   ```
