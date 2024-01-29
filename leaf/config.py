import os
import json
import secrets


def loadConfig():
    configFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    with open(configFile) as inFile:
        config = json.load(inFile)
    return config, configFile


class Config:
    config, configFile = loadConfig()

    # ConfigFile
    CONFIG_FILE = configFile

    # LeafCMS Folder
    LEAFCMS_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    SECRET_KEY = secrets.token_hex(32 // 2)

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

    # Deployments Servers
    DEPLOYMENTS_SERVERS = config["DEPLOYMENTS_SERVERS"]

    # Webserver Folder
    WEBSERVER_FOLDER = config["WEBSERVER_FOLDER"] + "/" if config["WEBSERVER_FOLDER"][-1] != "/" else config["WEBSERVER_FOLDER"]

    # User email assigned
    ASSIGNED_USER_EMAIL = config["ASSIGNED_USER_EMAIL"]

    # SMTP Details
    SMTP_HOST = config["SMTP_HOST"]
    SMTP_PORT = config["SMTP_PORT"]
    SMTP_USER = config["SMTP_USER"]
    SMTP_PASSWORD = config["SMTP_PASSWORD"]

    # Preview Webserver URL
    PREVIEW_SERVER = config["PREVIEW_SERVER"]
    PREVIEW_SERVER_PATH = config["WEBSERVER_FOLDER"]

    # Main Webserver URL
    MAIN_SERVER = config["MAIN_SERVER"]

    # Original Images webfolder
    ORIGINAL_IMAGES_WEBPATH = os.path.join(PREVIEW_SERVER, config["ORIGINAL_IMAGES_WEBPATH"])

    # Heritrix
    HERITRIX_FOLDER = config["HERITRIX_FOLDER"]
    HERITRIX_PORT = config["HERITRIX_PORT"]
    HERITRIX_USER = config["HERITRIX_USER"]
    HERITRIX_PASS = config["HERITRIX_PASS"]

    # Environment
    ENV_PATH = config["ENV_PATH"]

    # SSO
    SP_ENTITY_ID = config["SP_ENTITY_ID"]
    SP_ASSERTION_CONSUMER_SERVICE_URL = config["SP_ASSERTION_CONSUMER_SERVICE_URL"]
    SP_SINGLE_LOGOUT_SERVICE_URL = config["SP_SINGLE_LOGOUT_SERVICE_URL"]
    SP_X509CERT = config["CRT_FILE"]
    SP_X509KEY = config["CRT_KEY"]
    IDP_ENTITY_ID = config["IDP_ENTITY_ID"]
    IDP_METADATA = config["IDP_METADATA"]
    IDP_SINGLE_SIGN_ON_SERVICE_URL = config["IDP_SINGLE_SIGN_ON_SERVICE_URL"]
    IDP_SINGLE_LOGOUT_SERVICE_URL = config["IDP_SINGLE_LOGOUT_SERVICE_URL"]
    IDP_X509CERT = config["IDP_X509CERT"]

    # Auto Generated
    DYNAMIC_PATH = os.path.join(WEBSERVER_FOLDER, "leaf_content", "lists")
    FILES_UPLOAD_FOLDER = os.path.join(LEAFCMS_FOLDER, "leaf", "static", "uploads")
    os.makedirs(FILES_UPLOAD_FOLDER, exist_ok=True)
    IMAGES_WEBPATH = FILES_UPLOAD_FOLDER.replace(LEAFCMS_FOLDER, "")
    WORKFLOW_FILES_UPLOAD_FOLDER = os.path.join(LEAFCMS_FOLDER, "leaf", "static", "workflow_attachments")
    os.makedirs(WORKFLOW_FILES_UPLOAD_FOLDER, exist_ok=True)
    WORKFLOW_IMAGES_WEBPATH = WORKFLOW_FILES_UPLOAD_FOLDER.replace(LEAFCMS_FOLDER, "")
    SCREENSHOTS_FOLDER = os.path.join(WEBSERVER_FOLDER, "leaf_content", "screenshots")
    TEMP_UPLOAD_FOLDER = os.path.join(LEAFCMS_FOLDER, "leaf", "temp_upload")
    os.makedirs(TEMP_UPLOAD_FOLDER, exist_ok=True)
