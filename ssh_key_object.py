import yaml


class SSHKeyObject(object):

    def __init__(self):
        self.ssh_keys = []
        self.username = None
        pass

    def add_keys(self, ssh_keys):
        if type(ssh_keys) is list:
            self.ssh_keys = ssh_keys
        elif type(ssh_keys) is str:
            self.ssh_keys = [ssh_keys]
        else:
            raise TypeError("SSH keys must be either 'list' or 'str'.")
    
    def set_username(self, username, replacement_character="_"):
        self.username = sanitize_username(username, replacement_character)

    def dump_authorized_keys(self):
        return "\n".join(self.ssh_keys) + "\n"

    def __str__(self):
        return "<SSHKeyObject for {}({} keys)>".format(self.username, len(self.ssh_keys))


def import_config(filename):
    with open(filename, 'r') as stream:
        try:
            return yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)


def sanitize_username(username, replacement_character="_"):
    if type(username) is str:
        return username.replace(".", replacement_character)
    else:
        raise TypeError("Username must be of type 'str'.")
