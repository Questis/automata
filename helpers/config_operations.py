import logging
import os
import re
import yaml
from helpers.gitlab_operations import GitlabServerConfig, GitlabGroupConfig


# Dictionary to translate logging levels in the config file
log_level_dict = {
    "info": logging.INFO,
    "warning": logging.WARN,
    "debug": logging.DEBUG,
}


class ConfigOps:
    """
    Responsible for parsing the configuration file for information relating to automata.
    """

    filename: str
    raw_config: dict
    gitlab_config: dict
    logging_config: dict
    api_token_env: str

    def __init__(self, filename: str, api_token_env: str = 'GL_API_TOKEN') -> None:
        """
        :param filename: Configuration file name
        :param api_token_env: Gitlab API token environment variable.
        """
        self.filename = filename
        self.raw_config = self.__import_config(filename)
        self.gitlab_config = self.raw_config['gitlab']['server']
        self.logging_config = self.raw_config['logging']
        self.api_token_env = api_token_env

    def get_logging_config(self) -> dict:
        """
        Returns the logging configuration contained in the `raw_config` variable after some massaging.
        :return: LoggingConfig object
        :raises COInvalidLogLevel: Thrown if log level isn't defined in the log level dictionary.
        """
        if self.logging_config["log_level"] not in log_level_dict.keys():
            raise COInvalidLogLevel
        return {
            "level": log_level_dict[self.logging_config['log_level']],
            "filename": self.logging_config['log_path'],
            "format": self.logging_config['log_format'],
        }

    def get_gitlab_config(self) -> GitlabServerConfig:
        """
        Returns the Gitlab configuration object for the GitlabOps
        :return: GitlabServerConfig object
        """
        # Get Gitlab Group information
        gitlab_group_data = list()
        group_info = self.raw_config['gitlab']['groups']
        for k, v in group_info.items():
            try:
                other_groups = v['other_groups']
            except KeyError:
                other_groups = list()
            temp = GitlabGroupConfig(
                gitlab_group=k,
                linux_group=v['linux_group'],
                sudoers_line=sanitize_sudoers_line(v['sudoers_line']),
                other_groups=other_groups,
            )
            gitlab_group_data.append(temp)

        # Token information
        try:
            token_info = self.gitlab_config['api_token']
        except KeyError:
            token_info = os.environ.get(self.api_token_env)

        # Gitlab Server config information
        return GitlabServerConfig(
            address=self.gitlab_config['api_address'],
            token=token_info,
            groups=gitlab_group_data,
            sudoers_file=self.gitlab_config['sudoers_file'],
            home_dir_path=self.gitlab_config['home_dir_path'],
        )

    @staticmethod
    def __import_config(filename: str) -> dict:
        """
        Parses the configuration file
        :param filename: The file to parse the configuration from
        :return: The contents of the configuration file after being parsed.
        """
        with open(filename, 'r') as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)


def sanitize_username(username: str) -> str:
    """
    Remove non-word characters from a username
    :param username: The username to sanitize
    :return: The sanitized username
    """
    illegal_chars = r'[^\w]'
    return re.sub(illegal_chars, '_', username)


def sanitize_sudoers_line(sudoers_line: str) -> str:
    """
    Sanitize the sudoers file line
    :param sudoers_line: The line of the sudoers file
    :return: The sanitized sudoers file line
    """
    illegal_chars = r'\s+'
    return re.sub(illegal_chars, ' ', sudoers_line)


class COError(Exception):
    pass


class COInvalidLogLevel(COError):
    pass
