import mysql.connector
from flask import Blueprint, render_template, session
from flask import request
import base64
import requests
import xmltodict

from leaf import Config

saml_route = Blueprint("saml_route", __name__)


@saml_route.route("/saml", methods=["GET", "POST"])
def idp_initiated():
    if request.method == "GET":
        return "Access Denied"

    if request.method == "POST":
        saml_response = request.form["SAMLResponse"]
        if saml_response.startswith("http"):
            # Retrieve the SAML response from the URL
            response = requests.get(saml_response)
            response.raise_for_status()
            saml_response = response.text

        data_dict = xmltodict.parse(base64.b64decode(saml_response))

        if data_dict["samlp:Response"][Config.SAML_PREFIX + "Issuer"]["#text"].lower().strip() != Config.IDP_ENTITY_ID.lower().strip():
            return "Access Denied"

        resp = data_dict["samlp:Response"][Config.SAML_PREFIX + "Assertion"][Config.SAML_PREFIX + "AttributeStatement"][Config.SAML_PREFIX + "Attribute"]

        email = None
        firstName = None
        lastName = None
        isAdmin = 0

        for item in resp:
            if item["@Name"] == ATTRIBUTE_PREFIX + "email":
                email = item.get(Config.SAML_PREFIX + "AttributeValue")
            elif item["@Name"] == ATTRIBUTE_PREFIX + "firstName":
                firstName = item.get(Config.SAML_PREFIX + "AttributeValue")
            elif item["@Name"] == ATTRIBUTE_PREFIX + "lastName":
                lastName = item.get(Config.SAML_PREFIX + "AttributeValue")
            elif item["@Name"] == ATTRIBUTE_PREFIX + "group":
                groups = [entry.lower() for entry in item.get(Config.SAML_PREFIX + "AttributeValue")]
                isAdmin = 1 if any("poweruser" in g for g in groups) else 0

        if email:
            if Config.IS_LOCAL == 'True':
                mydb = mysql.connector.connect(host=Config.DB_HOST, port=Config.DB_PORT, user=Config.DB_USER, password=Config.DB_PASS, database=Config.DB_NAME)
            else:
                mydb = mysql.connector.connect(host=Config.LFI_DB_HOST, port=Config.LFI_DB_PORT, user=Config.LFI_DB_USER, password=Config.LFI_DB_PASS, database=Config.LFI_DB_NAME)

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

            mycursor = mydb.cursor(dictionary=True)
            mycursor.execute(query, (email,))
            lfi_user = mycursor.fetchone()
            cursor.close()

            if not lfi_user:
                query = "INSERT INTO user(account_id, email, username, is_admin) VALUES(?, ?, ?, ?)"
                values = (3, email, email, isAdmin)
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
                    query = "UPDATE user SET is_admin = ? WHERE id = ?"
                    values = (isAdmin, lfi_user_id)
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
                session['accountName'] = lfi_user[5]
                session['is_admin'] = lfi_user[6]
                session['is_manager'] = lfi_user[7]

                msg = 'Logged in successfully!'
                msgClass = 'alert alert-success'

                if session['accountId'] == 1:
                    return render_template('list_lfi_accounts.html', userId=session['id'], username=session['username'], user_image=session['user_image'], accountId=session['accountId'], accountName=session['accountName'], is_admin=session['is_admin'], is_manager=session['is_manager'], msg=msg, msgClass=msgClass)
                else:
                    return render_template('sites.html', userId=session['id'], username=session['username'], user_image=session['user_image'], accountId=session['accountId'], accountName=session['accountName'], is_admin=session['is_admin'], is_manager=session['is_manager'], msg=msg, msgClass=msgClass)
            else:
                # Account doesnt exist or username/password incorrect
                msg = 'Incorrect username/password!'
                msgClass = 'alert alert-danger'
                return render_template('login.html', msg=msg, msgClass=msgClass)

        else:
            msg = 'Missing email!'
            msgClass = 'alert alert-danger'
            return render_template('login.html', msg=msg, msgClass=msgClass)
