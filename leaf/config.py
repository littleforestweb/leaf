import json
import os


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

    SECRET_KEY = config["SECRET_KEY"]

    # Environment
    ENV = config["ENV"]
    ENV_PATH = config["ENV_PATH"]

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

    # Server
    PORT = config["PORT"]
    DEBUG = config["DEBUG"]

    # Deployments Servers
    DEPLOYMENTS_SERVERS = config["DEPLOYMENTS_SERVERS"]

    # Main Webserver URL
    MAIN_SERVER = config["MAIN_SERVER"]
    # Preview Webserver URL
    PREVIEW_SERVER = config["PREVIEW_SERVER"]
    PREVIEW_SERVER_PATH = config["WEBSERVER_FOLDER"]

    # User email assigned
    ASSIGNED_USER_EMAIL = config["ASSIGNED_USER_EMAIL"]

    # SMTP Details
    SMTP_HOST = config["SMTP_HOST"]
    SMTP_PORT = config["SMTP_PORT"]
    SMTP_USER = config["SMTP_USER"]
    SMTP_PASSWORD = config["SMTP_PASSWORD"]

    # Dynamic Root Path
    DYNAMIC_PATH = config["DYNAMIC_PATH"] + "/" if config["DYNAMIC_PATH"][-1] != "/" else config["DYNAMIC_PATH"]

    # Folders
    LOG_FOLDER = config["LOG_FOLDER"] + "/" if config["LOG_FOLDER"][-1] != "/" else config["LOG_FOLDER"]
    if not os.path.exists(LOG_FOLDER):
        os.mkdir(LOG_FOLDER)
    WEBSERVER_FOLDER = config["WEBSERVER_FOLDER"] + "/" if config["WEBSERVER_FOLDER"][-1] != "/" else config["WEBSERVER_FOLDER"]
    TEMP_UPLOAD_FOLDER = config["TEMP_UPLOAD_FOLDER"] + "/" if config["TEMP_UPLOAD_FOLDER"][-1] != "/" else config["TEMP_UPLOAD_FOLDER"]
    if not os.path.exists(TEMP_UPLOAD_FOLDER):
        os.mkdir(TEMP_UPLOAD_FOLDER)
    SCREENSHOTS_FOLDER = config["SCREENSHOTS_FOLDER"] + "/" if config["SCREENSHOTS_FOLDER"][-1] != "/" else config["SCREENSHOTS_FOLDER"]
    if not os.path.exists(SCREENSHOTS_FOLDER):
        os.mkdir(SCREENSHOTS_FOLDER)
    FILES_UPLOAD_FOLDER = config["FILES_UPLOAD_FOLDER"]
    if not os.path.exists(FILES_UPLOAD_FOLDER):
        os.mkdir(FILES_UPLOAD_FOLDER)
    IMAGES_WEBPATH = config["IMAGES_WEBPATH"]
    ORIGINAL_IMAGES_WEBPATH = PREVIEW_SERVER + config["ORIGINAL_IMAGES_WEBPATH"]
    WORKFLOW_FILES_UPLOAD_FOLDER = config["WORKFLOW_FILES_UPLOAD_FOLDER"]
    if not os.path.exists(WORKFLOW_FILES_UPLOAD_FOLDER):
        os.mkdir(WORKFLOW_FILES_UPLOAD_FOLDER)
    WORKFLOW_IMAGES_WEBPATH = config["WORKFLOW_IMAGES_WEBPATH"]

    # Heritrix
    HERITRIX_FOLDER = config["HERITRIX_FOLDER"]
    HERITRIX_PORT = config["HERITRIX_PORT"]
    HERITRIX_USER = config["HERITRIX_USER"]
    HERITRIX_PASS = config["HERITRIX_PASS"]

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
