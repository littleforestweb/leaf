import base64
import os
import re

import werkzeug.utils
from defusedxml.lxml import fromstring
from flask import Blueprint, render_template, session, request
from flask import current_app
from lxml import etree
from signxml import XMLVerifier

from leaf import Config
from leaf.decorators import db_connection, generate_jwt

saml_route = Blueprint("saml_route", __name__)


def perform_additional_xml_checks(xml_data):
    # Check for unexpected tags or attributes
    allowed_tags = {
        'Assertion', 'Issuer', 'Subject', 'NameID', 'AttributeStatement',
        'Attribute', 'AttributeValue', 'Conditions', 'AuthnStatement',
        'Response', 'Status', 'StatusCode', 'Signature'
    }

    allowed_attributes = {
        'Name', 'Format', 'InResponseTo', 'Version', 'IssueInstant', 'Method'
    }

    for element in xml_data.iter():
        # Check if the tag is in the allowed list
        if element.tag not in allowed_tags:
            return f'Invalid XML. {element.tag} tag found but not allowed!'

        # Check each attribute of the element
        for attribute in element.attrib:
            if attribute not in allowed_attributes:
                return f'Invalid XML. {attribute} attribute found but not allowed!'

    # Check for suspicious patterns (like script tags or SQL commands)
    if re.search(r'<script|SELECT\s+.*\s+FROM|INSERT\s+INTO', xml_data, re.IGNORECASE):
        return 'Invalid XML. Found Suspicious patterns!'

    # Validate namespaces
    for element in etree.fromstring(xml_data).iter():
        if element.tag.namespace not in namespaces:
            return f'Invalid XML. {element.tag.namespace} namespace found but not allowed!'

    # Remove or check comments
    comments = xml_data.xpath('//comment()')
    if comments:
        return 'Invalid XML. Comments found but not allowed!'

    return True


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
        print(response_str)
        # Check for any other malicious content or patterns
        additional_checks_validation = perform_additional_xml_checks(saml_response_xml)
        if additional_checks_validation is None or additional_checks_validation is False:
            # If validation fails, return a permission denied response
            return "Permission Denied. Saml response not valid!", 403

        return saml_response_xml
    except etree.XMLSyntaxError:
        # Handle malformed XML
        return False
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

    validate_saml_response = is_valid_saml_response(saml_response)
    if validate_saml_response is None or validate_saml_response is False:
        # If validation fails, return a permission denied response
        return "Permission Denied. Saml response not valid!", 403

    return validate_saml_response


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
        current_app.logger.info("Received GET")
        return "Access Denied"

    if request.method == "POST":
        current_app.logger.info("Received POST")

        # Load the IdP's metadata
        idp_metadata = etree.parse(Config.IDP_METADATA)

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

            saml_response_xml = process_saml_response(request.form["SAMLResponse"])
            if saml_response_xml is not False:
                current_app.logger.info('Saml Response is valid and secure!')
                # Extract the X509 certificate
                # Assuming that there's only one X509Certificate element in the SAML response
                response_cert_element = saml_response_xml.xpath("//*[local-name()='X509Certificate']")
                if response_cert_element:
                    cert_pem = f"-----BEGIN CERTIFICATE-----\n{idp_metadata_cert.strip()}\n-----END CERTIFICATE-----"
                    reponse_cert_pem = f"-----BEGIN CERTIFICATE-----\n{response_cert_element[0].text.strip()}\n-----END CERTIFICATE-----"

                    # Verify the signature using the certificate from the IdP metadata
                    try:
                        verified_data = XMLVerifier().verify(saml_response_xml, x509_cert=cert_pem).signed_xml
                        current_app.logger.info("Signature is valid.")
                    except Exception as e:
                        current_app.logger.info(f"Error verifying signature: {e}")
                        return "Access Denied. Error verifying signature!"
                else:
                    current_app.logger.info("Certificate not found in the SAML response. This connection might not be secure!")
                    return "Access Denied. Error verifying signature! Certificate not found in the SAML response."
        else:
            current_app.logger.info("X509Certificate element not found in the IdP metadata!")
            return "Access Denied. Error verifying signature! Certificate not found in the IdP metadata!"

        # issuer_text = saml_response_xml.xpath('//saml:Issuer', namespaces=namespaces)
        issuer_elements = saml_response_xml.xpath("//*[local-name() = 'Issuer']")
        if issuer_elements:
            issuer_text = issuer_elements[0].text

            if issuer_text and issuer_text.lower().strip() != Config.IDP_ENTITY_ID.lower().strip():
                return "Access Denied"

            # XPath query to get to the Attribute elements
            attributes = saml_response_xml.xpath("/samlp:Response/Assertion/AttributeStatement/Attribute", namespaces=namespaces)

            with open(os.path.join(Config.LEAFCMS_FOLDER, "resp.txt"), "w") as outFile:
                outFile.write(attributes)

            email = None
            username = None
            firstName = None
            lastName = None
            isAdmin = 0
            for item in attributes:
                # XPath query to find the Attribute element with Name="username"
                username_attribute = saml_response_xml.xpath("//saml:Attribute[@Name='username']/saml:AttributeValue", namespaces=namespaces)
                if username_attribute:
                    username = username_attribute[0].text
                # XPath query to find the Attribute element with Name="email"
                email_attribute = saml_response_xml.xpath("//saml:Attribute[@Name='email']/saml:AttributeValue", namespaces=namespaces)

                with open(os.path.join(Config.LEAFCMS_FOLDER, "resp.txt"), "w") as outFile:
                    outFile.write("email_attribute:" + email_attribute)

                if email_attribute:
                    email = username_attribute[0].text
                # XPath query to find the Attribute element with Name="firstName"
                firstName_attribute = saml_response_xml.xpath("//saml:Attribute[@Name='firstName']/saml:AttributeValue", namespaces=namespaces)
                if firstName_attribute:
                    firstName = firstName_attribute[0].text
                # XPath query to find the Attribute element with Name="lastName"
                lastName_attribute = saml_response_xml.xpath("//saml:Attribute[@Name='lastName']/saml:AttributeValue", namespaces=namespaces)
                if lastName_attribute:
                    lastName = lastName_attribute[0].text
                # XPath query to find the Attribute element with Name="group"
                group_values = saml_response_xml.xpath("//saml:Attribute[@Name='group']/saml:AttributeValue", namespaces=namespaces)
                groups = [value.text.lower() for value in group_values if value.text]
                isAdmin = 1 if any("poweruser" in group for group in groups) else 0

            if email:

                mydb, mycursor = db_connection()

                query = (
                    "SELECT user.id, "
                    "CASE WHEN image IS NOT NULL AND image <> '' THEN CONCAT('https://lfi.littleforest.co.uk/crawler/', image) "
                    "WHEN (image IS NULL OR image = '') AND color IS NOT NULL AND color <> '' THEN color ELSE '#176713' END AS user_image, "
                    "CASE WHEN (first_name IS NULL OR first_name = '') OR (last_name IS NULL OR last_name = '') THEN username "
                    "ELSE CONCAT(first_name, ' ', last_name) END AS username, "
                    "user.email, user.account_id, name, user.is_admin, user.is_manager "
                    "FROM user "
                    "LEFT JOIN user_image ON user_id = user.id "
                    "LEFT JOIN account ON user.account_id = account.id "
                    "WHERE email = %s"
                )

                try:

                    mycursor.execute(query, (email,))
                    lfi_user = mycursor.fetchone()

                    if not lfi_user:
                        query = "INSERT INTO user(account_id, email, username, is_admin) VALUES(?, ?, ?, ?)"
                        values = (3, email, username, isAdmin)
                        mycursor.execute(query, values)
                        mydb.commit()

                        user_id = mycursor.lastrowid

                        query = "INSERT INTO user_image(user_id, first_name, last_name) VALUES(?, ?, ?)"
                        values = (user_id, firstName, lastName)
                        mycursor.execute(query, values)
                        mydb.commit()

                        mycursor.execute(query, (email,))
                        lfi_user = mycursor.fetchone()

                    if lfi_user:
                        if lfi_user[6] != isAdmin:
                            query = "UPDATE user SET is_admin = %s WHERE id = %s"
                            values = (isAdmin, lfi_user[0])
                            mycursor.execute(query, values)
                            mydb.commit()

                    # If account exists in accounts table in out database
                    if lfi_user:
                        # Create session data, we can access this data in other routes
                        session['loggedin'] = True
                        session['id'] = lfi_user[0]
                        session['user_image'] = lfi_user[1]
                        session['username'] = lfi_user[2]
                        session['email'] = lfi_user[3]
                        session['accountId'] = lfi_user[4]
                        session['accountName'] = '' if lfi_user[5] is None else lfi_user[5]
                        session['is_admin'] = lfi_user[6]
                        session['is_manager'] = lfi_user[7]
                        session['logout_redirect'] = logout_redirect

                        # Generate and store JWT token in the session
                        jwt_token = generate_jwt()
                        session['jwt_token'] = jwt_token

                        msg = 'Logged in successfully!'
                        msgClass = 'alert alert-success'
                        return render_template('sites.html', userId=session['id'], username=session['username'],
                                               user_image=session['user_image'], accountId=session['accountId'],
                                               accountName=session['accountName'], is_admin=session['is_admin'],
                                               is_manager=session['is_manager'], msg=msg, msgClass=msgClass,
                                               jwt_token=jwt_token)
                    else:
                        # Account doesnt exist or username/password incorrect
                        msg = 'Incorrect username/password!'
                        msgClass = 'alert alert-danger'
                        return render_template('login.html', msg=msg, msgClass=msgClass)

                except Exception as e:
                    # Log the error or provide more details
                    print(f"Error during login: {e}")
                    msg = 'An error occurred during login.'
                    msgClass = 'alert alert-danger'
                    return render_template('login.html', msg=msg, msgClass=msgClass)
                finally:
                    mydb.close()

            else:
                msg = 'Missing email!'
                msgClass = 'alert alert-danger'
                return render_template('login.html', msg=msg, msgClass=msgClass)
        else:
            print("Issuer element not found.")
            return "Access Denied. Issuer not found!"


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
