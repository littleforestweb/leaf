import base64
import re

import requests
import werkzeug.utils
from defusedxml.lxml import fromstring
from flask import Blueprint, render_template, session, request, redirect, Response
from lxml import etree
from saml2 import BINDING_HTTP_POST
from saml2 import BINDING_HTTP_REDIRECT
from saml2 import config
from saml2 import metadata
from saml2.client import Saml2Client
from signxml import XMLVerifier
from urllib.parse import urlparse

from leaf import Config
from leaf.decorators import db_connection, generate_jwt
from leaf.groups import models as groups_model

saml_route = Blueprint("saml_route", __name__)


@saml_route.route('/saml/login')
def sp_saml_login():
    url_to_redirect_after_saml_login = request.args.get('url_to_redirect', '')
    # Parse the URL to extract components
    parsed_url = urlparse(url_to_redirect_after_saml_login)
    # Construct the base URL
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    if (base_url + "/saml" != Config.SP_ASSERTION_CONSUMER_SERVICE_URL):
        url_to_redirect_after_saml_login = ""

    if Config.IDP_METADATA != "":
        saml_client = Saml2Client(config=pysaml2_config(Config.SP_ASSERTION_CONSUMER_SERVICE_URL, url_to_redirect_after_saml_login))
        # Prepare the SAML Authentication Request
        _, info = saml_client.prepare_for_authenticate()
        redirect_url = dict(info["headers"])["Location"]
        return redirect(redirect_url)
    else:
        print("IDP Metadata not defined!")
        return "IDP Metadata not defined!"


@saml_route.route('/saml/metadata')
def saml_metadata():
    if Config.SP_ENTITY_ID != "":
        cfg = pysaml2_config(Config.SP_ASSERTION_CONSUMER_SERVICE_URL, "")
        # Use the metadata service to get the metadata as a string
        metadata_string = metadata.create_metadata_string(None, cfg, sign=True, valid=365 * 24)  # Generate metadata
        return Response(metadata_string, mimetype='text/xml')
    else:
        print("SP Entity ID not defined!")
        return "SP Entity ID not defined!"


@saml_route.route("/saml", methods=["GET", "POST"])
def idp_initiated():
    """
    Handle Identity Provider (IdP) initiated SAML authentication.

    This route processes SAML responses for user authentication.
    If accessed via GET method, it denies access. When accessed via POST, it processes the SAML response.
    The function performs several key actions:
    - Parses IdP metadata to find the X509Certificate and SingleLogoutService details.
    - Validates the SAML response signature using the X509Certificate.
    - Extracts user attributes (like email, username) from the SAML response.
    - Checks the user's existence in the database, creates a new user if not existing, and updates user data.
    - Sets session data for the authenticated user.
    - Redirects the user to the appropriate page based on the authentication result.

    Returns:
    - Response: A rendered template or a redirect, depending on the authentication outcome and method of request.
    """
    if request.method == "GET":
        return "Access Denied"

    if request.method == "POST":

        # Load the IdP's metadata
        # Fetch the content from the URL
        idp_metadata_response = requests.get(Config.IDP_METADATA)
        if idp_metadata_response.status_code == 200:
            # Parse the XML from the fetched content
            idp_metadata = etree.fromstring(idp_metadata_response.content)
        else:
            print("Failed to retrieve the IDP Metadata file: HTTP Status", response.status_code)
            return "Failed to retrieve the IDP Metadata file: HTTP Status", 403

        # Find the X509Certificate element (assuming there's only one)
        # Note: '{http://www.w3.org/2000/09/xmldsig#}X509Certificate' is the full tag name with namespace
        cert_elem = idp_metadata.find(".//ds:X509Certificate", namespaces=namespaces)

        # Find the SingleLogoutService element
        slo_elements = idp_metadata.findall(".//md:SingleLogoutService", namespaces=namespaces)

        for slo in slo_elements:
            # Extract attributes like Binding and Location from the SingleLogoutService element
            binding = slo.get('Binding')
            location = slo.get('Location')
            logout_redirect = False
            if binding == 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect':
                logout_redirect = location

        if cert_elem is not None:
            # Get the text of the X509Certificate element, which is base64 encoded
            idp_metadata_cert = cert_elem.text
            saml_response_xml, attributes_elements = process_saml_response(request.form["SAMLResponse"])
            if saml_response_xml is not False:
                print('Saml Response is valid and secure!')
                # Extract the X509 certificate
                # Assuming that there's only one X509Certificate element in the SAML response
                response_cert_element = saml_response_xml.xpath("//*[local-name()='X509Certificate']")
                if response_cert_element:
                    cert_pem = f"-----BEGIN CERTIFICATE-----\n{idp_metadata_cert.strip()}\n-----END CERTIFICATE-----"
                    reponse_cert_pem = f"-----BEGIN CERTIFICATE-----\n{response_cert_element[0].text.strip()}\n-----END CERTIFICATE-----"

                    # Verify the signature using the certificate from the IdP metadata
                    try:
                        verified_data = XMLVerifier().verify(saml_response_xml, x509_cert=cert_pem).signed_xml
                        print("Signature is valid.")
                    except Exception as e:
                        print(f"Error verifying signature: {e}")
                        return "Access Denied. Error verifying signature!", 403
                else:
                    print("Certificate not found in the SAML response. This connection might not be secure!")
                    return "Access Denied. Error verifying signature! Certificate not found in the SAML response.", 403
            else:
                print(f"Permission Denied. Saml response not valid!")
                return f"Permission Denied. Saml response not valid!", 403

        else:
            print("X509Certificate element not found in the IdP metadata!")
            return "Access Denied. Error verifying signature! Certificate not found in the IdP metadata!", 403

        # issuer_text = saml_response_xml.xpath('//saml:Issuer', namespaces=namespaces)
        issuer_elements = saml_response_xml.xpath("//*[local-name() = 'Issuer']")
        if issuer_elements:
            issuer_text = issuer_elements[0].text

            if issuer_text and issuer_text.lower().strip() != Config.IDP_ENTITY_ID.lower().strip():
                return "Access Denied"

            email = None
            username = None
            first_name = None
            last_name = None
            display_name = None
            isAdmin = 0

            attributes = {}

            for attr in attributes_elements:
                if attr['Name'] in Config.SAML_ATTRIBUTES_MAP:
                    attributes[Config.SAML_ATTRIBUTES_MAP[attr['Name']]] = attr['AttributeValue']

            email = attributes.get('email')
            username = attributes.get('username', email)
            first_name = attributes.get('firstName')
            last_name = attributes.get('lastName')
            display_name = attributes.get('displayName')

            group_values = attributes.get('group')
            groups = []
            if group_values is not None:
                if isinstance(group_values, str):
                    # If it's a string, split it into a list by commas
                    groups = group_values.split(',')

                # Ensure the groups are stripped of leading/trailing whitespace
                groups = [group.strip() for group in groups]
                isAdmin = 1 if any(Config.POWER_USER_GROUP == group for group in groups) else 0

            if email:

                mydb, mycursor = db_connection()

                main_query = (
                    "SELECT user.id, "
                    "CASE WHEN image IS NOT NULL AND image <> '' THEN CONCAT('https://lfi.littleforest.co.uk/crawler/', image) "
                    "WHEN (image IS NULL OR image = '') AND color IS NOT NULL AND color <> '' THEN color ELSE '#176713' END AS user_image, "
                    "CASE WHEN (first_name IS NULL OR first_name = '') AND (last_name IS NULL OR last_name = '') THEN username "
                    "ELSE CONCAT(first_name, ' ', last_name) END AS username, "
                    "user.email, user.account_id, name, user.is_admin, user.is_manager, user_image.first_name, user_image.last_name, user_image.display_name "
                    "FROM user "
                    "LEFT JOIN user_image ON user_id = user.id "
                    "LEFT JOIN account ON user.account_id = account.id "
                    "WHERE email = %s"
                )

                try:

                    mycursor.execute(main_query, (email,))
                    lfi_user = mycursor.fetchone()
                    mydb.commit()

                    if not lfi_user:
                        insert_user_query = "INSERT INTO user(account_id, email, username, is_admin) VALUES(%s, %s, %s, %s)"
                        insert_user_values = (Config.ACCOUNT_ID, email, username, isAdmin)
                        mycursor.execute(insert_user_query, insert_user_values)
                        mydb.commit()

                        user_id = mycursor.lastrowid

                        insert_user_details_query = "INSERT INTO user_image(user_id, first_name, last_name, display_name) VALUES(%s, %s, %s, %s)"
                        insert_user_details_values = (user_id, first_name, last_name, display_name)
                        mycursor.execute(insert_user_details_query, insert_user_details_values)
                        mydb.commit()

                        mycursor.execute(main_query, (email,))
                        lfi_user = mycursor.fetchone()
                        mydb.commit()

                    # If account exists in accounts table in out database
                    if lfi_user:

                        # First, check if the user_id already exists in the database
                        check_user_exists_query = "SELECT COUNT(*) FROM user_image WHERE user_id = %s"
                        check_user_exists_values = (lfi_user[0],)
                        mycursor.execute(check_user_exists_query, check_user_exists_values)
                        user_details_exists = mycursor.fetchone()[0] > 0

                        if not user_details_exists:
                            # If user_id does not exist, insert the new user details
                            insert_user_details_query = "INSERT INTO user_image(user_id, first_name, last_name, display_name) VALUES(%s, %s, %s, %s)"
                            insert_user_details_values = (lfi_user[0], first_name, last_name, display_name)
                            mycursor.execute(insert_user_details_query, insert_user_details_values)
                            mydb.commit()
                        else:
                            # If user_id exists, update the existing user details
                            update_user_details_query = "UPDATE user_image SET first_name = %s, last_name = %s, display_name = %s WHERE user_id = %s"
                            update_user_details_values = (first_name, last_name, display_name, lfi_user[0])
                            mycursor.execute(update_user_details_query, update_user_details_values)
                            mydb.commit()

                        if lfi_user[6] != isAdmin:
                            update_user_is_admin_query = "UPDATE user SET is_admin = %s WHERE id = %s"
                            update_user_is_admin_values = (isAdmin, lfi_user[0])
                            mycursor.execute(update_user_is_admin_query, update_user_is_admin_values)
                            mydb.commit()

                        mycursor.execute(main_query, (email,))
                        lfi_user = mycursor.fetchone()
                        mydb.commit()

                        leaf_user_groups = groups_model.get_all_user_groups(lfi_user[4])

                        # SQL query to check if an entry already exists
                        check_query = "SELECT * FROM group_member WHERE group_id=%s AND user_id=%s"
                        # SQL query to insert a new record
                        insert_query = "INSERT INTO group_member(group_id, user_id) VALUES (%s, %s)"
                        # SQL query to delete a new record
                        delete_query = "DELETE FROM group_member WHERE group_id=%s AND user_id=%s"

                        for group in groups:
                            if group in leaf_user_groups:
                                # Get the corresponding group_id
                                group_id = leaf_user_groups[group]
                                # Check if this user is already a member of this group
                                mycursor.execute(check_query, (group_id, lfi_user[0]))
                                result = mycursor.fetchone()
                                mydb.commit()
                                if not result:  # If there is no such record, insert it
                                    mycursor.execute(insert_query, (group_id, lfi_user[0]))
                                    mydb.commit()
                                    print(f"Inserted '{group}' into group_member.")
                                else:
                                    print(f"Skipped inserting '{group}' as it already exists.")

                        # Remove entries for groups no longer present
                        # First, fetch all groups associated with the user
                        mycursor.execute("SELECT group_id FROM group_member WHERE user_id=%s", (lfi_user[0],))
                        existing_groups_for_this_user = mycursor.fetchall()
                        mydb.commit()

                        # Create a set of current group IDs for fast lookup
                        current_group_ids = set(leaf_user_groups[group] for group in groups if group in leaf_user_groups)

                        # Check and remove any group not in the current list
                        for (group_id,) in existing_groups_for_this_user:
                            if group_id not in current_group_ids:
                                mycursor.execute(delete_query, (group_id, lfi_user[0]))
                                mydb.commit()
                                print(f"Removed group_id {group_id} for user_id {lfi_user[0]} as it is no longer in the current groups.")

                        # Create session data, we can access this data in other routes
                        session['loggedin'] = True
                        session['id'] = lfi_user[0]
                        session['first_name'] = lfi_user[8]
                        session['last_name'] = lfi_user[9]
                        session['display_name'] = lfi_user[10]
                        session['user_image'] = lfi_user[1]
                        session['username'] = lfi_user[2]
                        session['email'] = lfi_user[3]
                        session['accountId'] = lfi_user[4]
                        session['accountName'] = '' if lfi_user[5] is None else lfi_user[5]
                        session['is_admin'] = isAdmin
                        session['is_manager'] = lfi_user[7]
                        session['logout_redirect'] = logout_redirect

                        # Generate and store JWT token in the session
                        jwt_token = generate_jwt()
                        session['jwt_token'] = jwt_token

                        msg = 'Logged in successfully!'
                        msgClass = 'alert alert-success'
                        return render_template('sites.html', userId=session['id'], email=session['email'], username=session['username'],
                                               first_name=session['first_name'], last_name=session['last_name'], display_name=session['display_name'],
                                               user_image=session['user_image'], accountId=session['accountId'],
                                               accountName=session['accountName'], is_admin=session['is_admin'],
                                               is_manager=session['is_manager'], msg=msg, msgClass=msgClass,
                                               jwt_token=jwt_token, site_notice=Config.SITE_NOTICE)
                    else:
                        # Account doesnt exist or username/password incorrect
                        msg = 'Incorrect username/password!'
                        msgClass = 'alert alert-danger'
                        return render_template('login.html', msg=msg, msgClass=msgClass, is_saml_active=Config.SAML_ACTIVE)

                except Exception as e:
                    # Log the error or provide more details
                    print(f"Error during login: {e}")
                    msg = 'An error occurred during login.'
                    msgClass = 'alert alert-danger'
                    return render_template('login.html', msg=msg, msgClass=msgClass, is_saml_active=Config.SAML_ACTIVE)
                finally:
                    mydb.close()

            else:
                msg = 'Missing email!'
                msgClass = 'alert alert-danger'
                return render_template('login.html', msg=msg, msgClass=msgClass, is_saml_active=Config.SAML_ACTIVE)
        else:
            print("Issuer element not found.")
            return "Access Denied. Issuer not found!"


def perform_additional_xml_checks(xml_data):
    # Check for unexpected tags or attributes
    allowed_tags = {
        'Assertion', 'Issuer', 'Subject', 'NameID', 'AttributeStatement',
        'Attribute', 'AttributeValue', 'Conditions', 'AuthnStatement',
        'Response', 'Status', 'StatusCode', 'Signature', 'SignedInfo',
        'CanonicalizationMethod', 'SignatureMethod', 'Reference', 'Transforms',
        'Transform', 'DigestMethod', 'DigestValue', 'DigestValueType', 'SignatureValue',
        'X509Data', 'X509Certificate', 'EncryptedAssertion', 'EncryptedData',
        'EncryptedKey', 'EncryptedAttribute', 'EncryptionMethod', 'KeyDescriptor',
        'KeyInfo', 'KeyName', 'KeyInfoReference', 'KeyValue', 'MgmtData',
        'AuthenticatingAuthority', 'AuthenticatingAuthorityRef',
        'AssertionIDRef', 'AssertionURIRef', 'AssertionURI', 'NameIDPolicy',
        'AuthnRequest', 'AuthnResponse', 'LogoutRequest', 'LogoutResponse',
        'ManageNameIDResponse', 'NewEncryptedID', 'NewID', 'IDPList', 'IDPEntry',
        'AffiliationDescriptor', 'AttributeAuthorityDescriptor',
        'AuthnAuthorityDescriptor', 'PDPDescriptor', 'RoleDescriptor',
        'ServiceDescription', 'ServiceName', 'ServiceDisplayName',
        'AssertionConsumerService', 'AttributeService', 'AuthzService',
        'ManageNameIDService', 'ArtifactResolutionService', 'AssertionIDRequestService',
        'NameIDMappingService', 'NameIDManagementService', 'AttributeQueryService', 'BatchRequest',
        'BatchResponse', 'Request', 'IDPSSODescriptor', 'AttributeConsumingService',
        'NameIDMappingRequest', 'AttributeQuery', 'AuthnQuery', 'ArtifactResponse',
        'LogoutNotification', 'AuthzDecisionStatement', 'Action', 'Evidence', 'DoNotCacheCondition',
        'AuthnContext', 'AuthnContextClassRef', 'AuthnContextDeclRef', 'AuthnContextDecl', 'RequestedAuthnContext',
        'ArtifactResolve', 'AssertionIDRequest', 'AuthzDecisionQuery', 'ManageNameIDRequest',
        'SubjectConfirmation', 'SubjectConfirmationData', 'AudienceRestriction', 'Audience',
        'CipherData', 'CipherValue'
    }

    allowed_attributes = {
        'id', 'name', 'format', 'nameformat', 'inresponseto', 'version',
        'issueinstant', 'method', 'type', 'algorithm', 'uri', 'notonorafter',
        'recipient', 'destination', 'value', 'notbefore', 'authninstant', 'sessionindex'
    }

    xpath_expressions = [
        ".//ns0:Assertion", ".//ns1:Assertion", ".//saml2:EncryptedAssertion",
        ".//*[local-name()='Assertion']"
    ]

    # Extract namespace dynamically for Assertion
    # Find Assertion element using XPath expressions
    assertion_element = None
    for xpath_expression in xpath_expressions:
        assertion_elements = xml_data.xpath(xpath_expression, namespaces=namespaces)
        if assertion_elements:
            assertion_element = assertion_elements[0]
            break

    if assertion_element is None:
        print('No Assertion element found!')
        return False

    # Get the namespace of the Assertion element
    assertion_namespace = assertion_element.tag.split('}')[0][1:]

    attributes_elements = []
    for element in xml_data.iter():
        # Check if the tag is in the allowed list
        namespace, this_tag = element.tag[1:].split('}')

        # Validate namespaces
        if namespace not in namespaces.values():
            print(f'Invalid XML. {namespace} namespace found but not allowed!')
            return False

        if this_tag not in allowed_tags:
            print(f'Invalid XML. {this_tag} tag found but not allowed!')
            return False

        # Extract Name and NameFormat attributes
        if element.tag.endswith('}Attribute'):
            name = element.get('Name')
            name_format = element.get('NameFormat', '')

            # Find all AttributeValue elements under the current Attribute element
            attribute_values = element.findall('{*}AttributeValue')

            # Extract text from each AttributeValue and create a list of those values
            attribute_value_texts = [attr_value.text.strip() for attr_value in attribute_values]

            # Depending on your use case, you can join these values into a single string or keep them as a list
            # For example, joining with a comma:
            attribute_value_joined = ', '.join(attribute_value_texts)

            # Add extracted information to the array
            attributes_elements.append({
                'Name': name,
                'NameFormat': name_format,
                'AttributeValue': attribute_value_joined
            })

        # Check each attribute of the element
        for attribute, value in element.attrib.items():
            # Split the attribute to separate namespace and attribute name
            if '}' in attribute:
                attr_namespace, attr_name = attribute[1:].split('}')  # Remove the leading '{'
            else:
                attr_namespace = ''
                attr_name = attribute

            # Check if the attribute namespace is in the predefined namespaces
            if attr_namespace and attr_namespace not in namespaces.values():
                print(f'Invalid XML. Attribute Namespace {attr_namespace} not allowed!')
                return False

            # Check if the attribute name is in the allowed attributes
            if attr_name.lower() not in allowed_attributes:
                print(f'Invalid XML. {attr_name} attribute found but not allowed!')
                return False

    # Check for suspicious patterns (like script tags or SQL commands)
    if re.search(r'<script|SELECT\s+.*\s+FROM|INSERT\s+INTO', etree.tostring(xml_data).decode(), re.IGNORECASE):
        print(f'Invalid XML. Found Suspicious patterns!')
        return False

    # Remove or check comments
    comments = xml_data.xpath('//comment()')
    if comments:
        print('Invalid XML. Comments found but not allowed!')
        return False

    return attributes_elements


def is_valid_saml_response(saml_response):
    """
    Validates the SAML response for correct XML structure and checks for injection attacks.

    Args:
        saml_response (str): The Base64 encoded SAML response.

    Returns:
        bool: True if the SAML response is valid, False otherwise.
    """
    try:
        # Decode the SAML response
        response_str = base64.b64decode(saml_response).decode('utf-8')

        # Parse the XML
        # Using defusedxml is a better option for handling externally provided XML data that might be untrusted or potentially malicious
        saml_response_xml = fromstring(response_str.encode('utf-8'))

        # Optional: Schema validation can be performed here if an XSD is available
        # Check for any other malicious content or patterns
        attributes_elements = perform_additional_xml_checks(saml_response_xml)
        if attributes_elements is None or attributes_elements is False:
            # If validation fails, return a permission denied response
            return [False, False]

        return [saml_response_xml, attributes_elements]
    except etree.XMLSyntaxError:
        # Handle malformed XML
        return [False, False]
    # Add more exceptions as necessary for different types of checks


def process_saml_response(saml_response_from_request):
    """
    Process the SAML response from a request.

    Args:
        request (Request): The HTTP request object.

    Returns:
        Response: The appropriate HTTP response.
    """
    # Read SAMLRequest and escape special characters in the string it receives to prevent injection attacks
    saml_response = werkzeug.utils.escape(saml_response_from_request)

    validate_saml_response, attributes_elements = is_valid_saml_response(saml_response)
    if validate_saml_response is None or validate_saml_response is False:
        # If validation fails, return a permission denied response
        return [False, False]

    return [validate_saml_response, attributes_elements]


def pysaml2_config(SP_ASSERTION_CONSUMER_SERVICE_URL, url_to_redirect_after_saml_login):
    cfg = {
        "entityid": Config.SP_ENTITY_ID,
        "service": {
            "sp": {
                "endpoints": {
                    "assertion_consumer_service": [
                        (SP_ASSERTION_CONSUMER_SERVICE_URL + "?RelayState=" + url_to_redirect_after_saml_login, BINDING_HTTP_POST),
                    ],
                    "single_logout_service": [
                        (Config.SP_SINGLE_LOGOUT_SERVICE_URL, BINDING_HTTP_REDIRECT),
                    ],
                },
                "allow_unsolicited": True,
                "authn_requests_signed": False,
                "logout_requests_signed": True,
                "want_assertions_signed": True,
                "want_response_signed": True,
            }
        },
        "metadata": {
            "remote": [{
                "url": Config.IDP_METADATA,
                "cert": None,  # Optional: Path to a certificate file to verify the HTTPS connection
            }]
        },
        "xmlsec_binary": Config.XMLSEC_BINARY,
        "key_file": Config.SP_X509KEY,
        "cert_file": Config.SP_X509CERT
    }

    sp_config = config.SPConfig()
    sp_config.load(cfg)
    return sp_config


namespaces = {
    'md': 'urn:oasis:names:tc:SAML:2.0:metadata',
    'spml': 'urn:oasis:names:tc:SPML:2:0',

    # Common SAML namespaces with different prefixes
    'saml': 'urn:oasis:names:tc:SAML:2.0:assertion',
    'saml2': 'urn:oasis:names:tc:SAML:2.0:assertion',
    'samlp': 'urn:oasis:names:tc:SAML:2.0:protocol',

    # XML Signature and Encryption namespaces
    'ds': 'http://www.w3.org/2000/09/xmldsig#',
    'xenc': 'http://www.w3.org/2001/04/xmlenc#',

    # XML Schema namespaces
    'xs': 'http://www.w3.org/2001/XMLSchema',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',

    # SOAP namespace
    'soap': 'http://schemas.xmlsoap.org/soap/envelope/',

    # WS-Security and related namespaces
    'wsu': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd',
    'wsse': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd',
    'wsp': 'http://schemas.xmlsoap.org/ws/2004/09/policy',
    'wsa': 'http://www.w3.org/2005/08/addressing',

    # Other namespaces
    'wsdl': 'http://schemas.xmlsoap.org/wsdl/',
    'xlink': 'http://www.w3.org/1999/xlink',

    # Generic namespaces (can be adjusted as needed)
    'ns0': 'urn:oasis:names:tc:SAML:2.0:protocol',
    'ns1': 'urn:oasis:names:tc:SAML:2.0:assertion',
    'ns2': 'http://www.w3.org/2001/04/xmlenc#',
    'ns3': 'http://www.w3.org/2000/09/xmldsig#',
    'ns4': 'http://schemas.xmlsoap.org/soap/envelope/',
    # ... and so on for other generic namespaces
}
