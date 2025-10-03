import json
import os
import secrets

from git import Repo


def checkConfig(loaded_json):
    """
    Validates and updates the provided JSON configuration with the expected structure.

    Parameters:
    - loaded_json (dict): The loaded JSON configuration to be checked and updated.

    Returns:
    dict: The validated and updated JSON configuration, conforming to the expected structure.

    The function compares the provided JSON configuration with the expected structure and:
    1. Adds missing keys with their default values.
    2. Recursively updates nested dictionaries.
    3. Removes keys that are not part of the expected structure.

    The expected structure includes configuration keys for various settings such as database,
    deployment servers, web server, email, and more.

    Note: The input loaded_json is modified in place, and the modified dictionary is returned.
    """

    # Set expected config.json
    expected_structure = {
        "DEBUG": False,
        "CORS_ALLOWED_ORIGINS": [],
        "CONTENT_SECURITY_POLICY": "",
        "ACCOUNT_ID": 1,
        "JWT_EXPIRATION_TIME": 24,
        "DB_HOST": "",
        "DB_PORT": 3306,
        "DB_USER": "",
        "DB_PASS": "",
        "DB_NAME": "",
        "DB_SOCKET": "",
        "DEPLOYMENTS_SERVERS": [
            {
                "name": "",
                "ip": "",
                "port": 22,
                "user": "",
                "pw": "",
                "pkey": "",
                "remote_path": "",
                "webserver_url": ""
            }
        ],
        "WEBSERVER_FOLDER": "",
        "ASSIGNED_USER_EMAIL": "",
        "EMAIL_METHOD": "SMTP",
        "SMTP_HOST": "",
        "SMTP_PORT": "",
        "SMTP_USER": "",
        "SMTP_PASSWORD": "",
        "PREVIEW_SERVER": "",
        "LEAFCMS_SERVER": "",
        "ORIGINAL_IMAGES_WEBPATH": "",
        "HERITRIX_FOLDER": "",
        "HERITRIX_PORT": "",
        "HERITRIX_USER": "",
        "HERITRIX_PASS": "",
        "SAML_ACTIVE": 0,
        "SP_ENTITY_ID": "",
        "SP_ASSERTION_CONSUMER_SERVICE_URL": "",
        "SP_SINGLE_LOGOUT_SERVICE_URL": "",
        "SP_METADATA": "",
        "SP_X509CERT": "",
        "SP_X509KEY": "",
        "IDP_ENTITY_ID": "",
        "IDP_METADATA": "",
        "IDP_SINGLE_SIGN_ON_SERVICE_URL": "",
        "IDP_SINGLE_LOGOUT_SERVICE_URL": "",
        "IDP_X509CERT": "",
        "SAML_ATTRIBUTES_MAP": {},
        "POWER_USER_GROUP": "admin",
        "SOURCE_EDITOR_USER_GROUP": "source_editor",
        "XMLSEC_BINARY": "",
        "SITE_NOTICE": "This is a site notice that you can control on your config.json file. Keep it empty to remove the notice!",
        "PAGES_EXTENSION": ".page",
        "EDITOR_ALLOW_SCRIPTS_REGEX_PATTERNS": [],
        "EDITOR_REPLACE_WITH_MAP": {}
    }

    # Update the loaded JSON with the expected structure
    def recursive_update(existing, expected):
        for key, value in expected.items():
            if key not in existing:
                existing[key] = value
            elif isinstance(value, dict) and isinstance(existing[key], dict):
                # Recursively update nested dictionaries
                recursive_update(existing[key], value)

    recursive_update(loaded_json, expected_structure)

    # Remove keys that are not in the expected structure
    loaded_json = {key: loaded_json[key] for key in expected_structure.keys() if key in loaded_json}

    return loaded_json


def loadConfig():
    """
    Loads and validates the configuration from the 'config.json' file.

    Returns:
    Tuple[dict, str]: A tuple containing the validated configuration dictionary and the path to the configuration file.

    This function reads the 'config.json' file, loads its contents into a dictionary,
    and then validates the configuration using the checkConfig function.
    The validated configuration is then saved back to the 'config.json' file with proper formatting.

    Returns the validated configuration dictionary and the path to the configuration file.
    """
    # Get the path to the 'config.json' file
    configFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

    # Check if file exists -> create it
    if not os.path.join(configFile):
        with open(configFile, "w") as outFile:
            json.dump({}, outFile, indent=2)

    # Read the configuration from the file
    with open(configFile, "r") as inFile:
        config = json.load(inFile)

    # Validate and update the configuration using the checkConfig function
    config = checkConfig(config)

    # Save the validated configuration back to the 'config.json' file
    with open(configFile, "w") as outFile:
        json.dump(config, outFile, indent=2)

    # Return the validated configuration and the path to the configuration file
    return config, configFile


class Config:
    config, configFile = loadConfig()

    # ConfigFile
    CONFIG_FILE = configFile

    # LeafCMS Folder
    LEAFCMS_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Generate SECRET_KEY
    secret_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "secret.key")
    if not os.path.exists(secret_file):
        with open(secret_file, "w") as out_file:
            out_file.write(secrets.token_hex(32 // 2))
    with open(secret_file) as in_file:
        SECRET_KEY = in_file.read()

    # DEBUG MODE
    DEBUG = config["DEBUG"]

    # CORS_ALLOWED_ORIGINS
    CORS_ALLOWED_ORIGINS = config["CORS_ALLOWED_ORIGINS"]

    # CONTENT SECURITY POLICY
    CONTENT_SECURITY_POLICY = config["CONTENT_SECURITY_POLICY"]

    # Client Account ID
    ACCOUNT_ID = config["ACCOUNT_ID"]

    # JWT Expiration time
    JWT_EXPIRATION_TIME = config["JWT_EXPIRATION_TIME"]

    # Database
    DB_HOST = config["DB_HOST"]
    DB_PORT = config["DB_PORT"]
    DB_USER = config["DB_USER"]
    DB_PASS = config["DB_PASS"]
    DB_NAME = config["DB_NAME"]
    DB_SOCKET = config["DB_SOCKET"]

    # Deployments Servers
    DEPLOYMENTS_SERVERS = config["DEPLOYMENTS_SERVERS"]

    # Webserver Folder
    WEBSERVER_FOLDER = config["WEBSERVER_FOLDER"]

    # Initialize the repository
    if os.path.exists(os.path.join(WEBSERVER_FOLDER, ".git")):
        GIT_REPO = Repo(WEBSERVER_FOLDER)

    # User email assigned
    ASSIGNED_USER_EMAIL = config["ASSIGNED_USER_EMAIL"]

    # SMTP Details
    EMAIL_METHOD = config["EMAIL_METHOD"]
    SMTP_HOST = config["SMTP_HOST"]
    SMTP_PORT = config["SMTP_PORT"]
    SMTP_USER = config["SMTP_USER"]
    SMTP_PASSWORD = config["SMTP_PASSWORD"]

    # Preview Webserver URL
    PREVIEW_SERVER = config["PREVIEW_SERVER"]

    # Main Webserver URL
    LEAFCMS_SERVER = config["LEAFCMS_SERVER"]

    # Original Images webfolder
    ORIGINAL_IMAGES_WEBPATH = os.path.join(PREVIEW_SERVER, config["ORIGINAL_IMAGES_WEBPATH"])

    # Heritrix
    HERITRIX_FOLDER = config["HERITRIX_FOLDER"]
    HERITRIX_PORT = config["HERITRIX_PORT"]
    HERITRIX_USER = config["HERITRIX_USER"]
    HERITRIX_PASS = config["HERITRIX_PASS"]

    # SSO
    SAML_ACTIVE = config["SAML_ACTIVE"]
    SP_ENTITY_ID = config["SP_ENTITY_ID"]
    SP_ASSERTION_CONSUMER_SERVICE_URL = config["SP_ASSERTION_CONSUMER_SERVICE_URL"]
    SP_SINGLE_LOGOUT_SERVICE_URL = config["SP_SINGLE_LOGOUT_SERVICE_URL"]
    SP_METADATA = config["SP_METADATA"]
    SP_X509CERT = config["SP_X509CERT"]
    SP_X509KEY = config["SP_X509KEY"]
    IDP_ENTITY_ID = config["IDP_ENTITY_ID"]
    IDP_METADATA = config["IDP_METADATA"]
    IDP_SINGLE_SIGN_ON_SERVICE_URL = config["IDP_SINGLE_SIGN_ON_SERVICE_URL"]
    IDP_SINGLE_LOGOUT_SERVICE_URL = config["IDP_SINGLE_LOGOUT_SERVICE_URL"]
    IDP_X509CERT = config["IDP_X509CERT"]
    SAML_ATTRIBUTES_MAP = config["SAML_ATTRIBUTES_MAP"]
    POWER_USER_GROUP = config["POWER_USER_GROUP"]
    XMLSEC_BINARY = config["XMLSEC_BINARY"]

    SITE_NOTICE = config["SITE_NOTICE"]
    PAGES_EXTENSION = config["PAGES_EXTENSION"]

    SOURCE_EDITOR_USER_GROUP = config["SOURCE_EDITOR_USER_GROUP"]

    # Auto Generated
    DYNAMIC_PATH = os.path.join("leaf_content", "lists")
    STATIC_FOLDER = os.path.join(LEAFCMS_FOLDER, "leaf", "static")
    LEAF_STATIC_FOLDER = os.path.join(LEAFCMS_FOLDER, "leaf", "leaf_static")
    os.makedirs(LEAF_STATIC_FOLDER, exist_ok=True)
    FILES_UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, "uploads")
    os.makedirs(FILES_UPLOAD_FOLDER, exist_ok=True)
    IMAGES_WEBPATH = FILES_UPLOAD_FOLDER.replace(LEAFCMS_FOLDER, "")
    WORKFLOW_FILES_UPLOAD_FOLDER = os.path.join(LEAF_STATIC_FOLDER, "workflow_attachments")
    os.makedirs(WORKFLOW_FILES_UPLOAD_FOLDER, exist_ok=True)
    WORKFLOW_IMAGES_WEBPATH = WORKFLOW_FILES_UPLOAD_FOLDER.replace(LEAFCMS_FOLDER, "")
    SCREENSHOTS_FOLDER = os.path.join(WEBSERVER_FOLDER, "leaf_content", "screenshots")
    TEMP_UPLOAD_FOLDER = os.path.join(LEAFCMS_FOLDER, "temp_upload")
    os.makedirs(TEMP_UPLOAD_FOLDER, exist_ok=True)
    ENV_PATH = TEMP_UPLOAD_FOLDER
    TEMPLATES_FOLDER = os.path.join(LEAFCMS_FOLDER, "templates_folder")
    os.makedirs(TEMPLATES_FOLDER, exist_ok=True)
    REMOTE_UPLOADS_FOLDER = os.path.join("leaf_content", "uploads")
    EDITOR_ALLOW_SCRIPTS_REGEX_PATTERNS = (
        config["EDITOR_ALLOW_SCRIPTS_REGEX_PATTERNS"][0]
        if len(config["EDITOR_ALLOW_SCRIPTS_REGEX_PATTERNS"]) == 1
        else "|".join(config["EDITOR_ALLOW_SCRIPTS_REGEX_PATTERNS"])
        if len(config["EDITOR_ALLOW_SCRIPTS_REGEX_PATTERNS"]) > 1
        else ""
    )
    EDITOR_REPLACE_WITH_MAP = config["EDITOR_REPLACE_WITH_MAP"]
