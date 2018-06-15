#!/usr/bin/env python3

from ssh_key_object import SSHKeyObject, import_config, sanitize_username
import grp
import json
import logging
import os
import pwd
import requests
import shlex
import subprocess
import sys

# Set the default shell
SHELL = "/bin/bash"

# Set the runtime directory to the directory the script actually lives in.  This
# is evidently very, very important.
working_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(working_dir)

# Import all of the configuration options from the YAML file.
config = import_config("automata.yaml")

# Quick translation table for logging levels and their corresponding constants
# from the 'logging' module.
log_level_dict = {
    "info": logging.INFO,
    "warning": logging.WARNING,
    "debug": logging.DEBUG,
}

# Logging configuration
log_level = log_level_dict[config["logging"]["log_level"]]
log_filename = config["logging"]["log_path"]
log_format = config["logging"]["log_format"]
logging.basicConfig(filename=log_filename, format=log_format, level=log_level)

# GitLab API and group information
gitlab_api_address = config["server"]["api_address"]
gitlab_api_token = {"private_token": config["server"]["api_token"]}
gitlab_group = config["server"]["group"]

# Linux group and user management information
group_tracking = config["group"]
# Sudoers file configuration
sudoers_file = config["sudoers_file"]

# Set hosts environment
host_env = os.environ.copy()
host_env["PATH"] = "/bin:/sbin:/usr/bin:/usr/sbin:" + host_env["PATH"]

# Get all members of a given group
api_path = "groups/{}/members".format(gitlab_group)
full_path = os.path.join(gitlab_api_address, api_path)
logging.debug("Querying users from {}.".format(full_path))
try:
    response = json.loads(requests.get(full_path, params=gitlab_api_token).text)
    if type(response) is dict:
        if "error" in response.keys():
            logging.warning("Error querying the API: {}".format(response["error_description"]))
            sys.exit(11)
        elif "message" in response.keys():
            logging.warning("Server error: {}".format(response["message"]))
            sys.exit(12)
        else:
            logging.warning("Unknown error: {}".format(response))
            sys.exit(13)
    try:
        members = [(i["id"], i["username"]) for i in response]
    except:
        members = []
except requests.exceptions.ConnectionError as e:
    logging.warning("Unable to connect to the Gitlab server: {}".format(e.message))
    sys.exit(10)

# Get associated SSH keys for a list of members
api_path = "users/{}/keys"
full_path = os.path.join(gitlab_api_address, api_path)
ssh_list = []
for member in members:
    sshobj = SSHKeyObject()
    logging.debug("Querying user SSH key information for {}".format(member[1]))
    response = json.loads(requests.get(full_path.format(member[0]), params=gitlab_api_token).text)
    keys = [i["key"] for i in response]
    logging.debug("Found {} keys, adding them to user.".format(len(keys)))
    sshobj.add_keys(keys)
    logging.debug("Setting the username to {}.".format(str(member[1])))
    sshobj.set_username(str(member[1]))
    logging.debug("Adding '{}' to the list.".format(sshobj))
    ssh_list.append(sshobj)

# Get list of user accounts in the automated group in the '/etc/group' file.
try:
    group = grp.getgrnam(group_tracking)
except KeyError:
    logging.info("Group not found, creating the '{}' group.".format(group_tracking))
    command = "groupadd {}".format(group_tracking)
    subprocess.check_call(shlex.split(command), env=host_env)
finally:
    group = grp.getgrnam(group_tracking)

# Grab the GID of the automated group.
group_tracking_gid = group[2]

# Now grab all of the user accounts in the '/etc/passwd' file that also fall under the automated
# group and combine them with the 'group' list
passwd = set([sanitize_username(i[0]) for i in pwd.getpwall() if i[3] == group_tracking_gid])
group = set([sanitize_username(i) for i in group[-1]])
current_users = group.union(passwd)

# Start removing users with extreme prejudice that are no longer in the GitLab group.
removed_users = current_users - set([i.username for i in ssh_list])
if len(removed_users) > 0:
    logging.info("Found {} users to delete: {}".format(len(removed_users), ", ".join(removed_users)))
else:
    logging.info("No users need to be removed.")

for user in removed_users:
    logging.info("Deleting user {}.".format(user))
    command = "userdel -f --remove {}".format(user)
    subprocess.check_call(shlex.split(command), env=host_env)

# Create any new users from the GitLab group
created_users = set([i.username for i in ssh_list]) - current_users
if len(created_users) > 0:
    logging.info("Found {} users to create: {}".format(len(created_users), ", ".join(created_users)))
else:
    logging.info("No users need to be created.")
    
for user in created_users:
    logging.info("Creating user {}.".format(user))
    command = "useradd -s {} -m -g {} {}".format(SHELL, group_tracking, user)
    subprocess.check_call(shlex.split(command), env=host_env)

# Regenerate _all_ SSH keys for the users that currently exist.
for ssh_obj in ssh_list:
    user = ssh_obj.username
    user_info = [i.dump_authorized_keys() for i in ssh_list if sanitize_username(i.username) == user][0]
    home_dir = "/home/{}/.ssh".format(user)
    key_path = os.path.join(home_dir, "authorized_keys")
    try:
        os.makedirs(home_dir)
    except OSError as e:
        logging.debug("Creating '{}': directory already exists, skipping.".format(home_dir))
    uid = pwd.getpwnam(user)[2]
    os.chown(home_dir, uid, group_tracking_gid)
    logging.info("Creating/updating the 'authorized_keys' file for user '{}'.".format(user))
    with open(key_path, "w") as f:
        f.write(user_info)
    os.chown(key_path, uid, group_tracking_gid)
    command = "chmod 0644 {}".format(key_path)
    logging.debug("Changing the mode of 'authorized_keys' to 0644 for user '{}'.".format(user))
    subprocess.check_call(shlex.split(command), env=host_env)

# Create entries in the /etc/sudoers.d directory
logging.info("Regenerating the '/etc/sudoers.d/{}' file.".format(sudoers_file))
with open("/etc/sudoers.d/{}".format(sudoers_file), "w") as f:
    template = "{} ALL=(ALL) NOPASSWD: ALL\n"
    [f.write(template.format(i)) for i in [j.username for j in ssh_list]]
