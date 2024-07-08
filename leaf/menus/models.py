# models.py

import csv
import html
import json
import os

import pandas as pd
import werkzeug.utils
from flask import jsonify, session

from leaf.config import Config
from leaf.decorators import db_connection
from leaf.sites.models import get_user_access_folder
from leaf.lists.models import add_column_if_not_exists


def get_menus_data(accountId: int, userId: str, isAdmin: str):
    """
    Get menus data from the database.

    Args:
        accountId (int): The account ID for which to retrieve menus data.
        isAdmin (str): A string indicating whether the user is an administrator (1 for admin, 0 for non-admin).

    Returns:
        dict: A JSON response containing menus data. The response includes a list of dictionaries, each
        representing a menu with keys 'id', 'name', 'reference', 'created', and 'user_with_access'.
    """
    jsonR = {'menus': []}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        sql = "SELECT menus.id, menus.name, menus.reference, menus.created, menus.user_with_access FROM menus WHERE accountId = %s"
        queryVal = (accountId,)
        mycursor.execute(sql, queryVal)

        menus = mycursor.fetchall()

        if session["is_admin"] == 0:
            groups_names = [gname.split('/')[1] for gname in get_user_access_folder()]
            menusLst = [
                {"id": singleMenu[0], "name": singleMenu[1], "reference": singleMenu[2], "created": singleMenu[3], "user_with_access": singleMenu[4]}
                for singleMenu in menus
                if any(group_name in singleMenu[2] for group_name in groups_names)
            ]
        else:
            menusLst = [
                {"id": singleMenu[0], "name": singleMenu[1], "reference": singleMenu[2], "created": singleMenu[3], "user_with_access": singleMenu[4]}
                for singleMenu in menus
            ]

        jsonR = {"menus": menusLst}

    except Exception as e:
        print("get_menus_data model")
        print(e)
    finally:
        mydb.close()
        return jsonify(jsonR)


def get_menu_details(accountId: str, reference: str):
    """
    Retrieve menu details for a specific account and reference.

    Args:
        accountId (str): The ID of the account requesting the menu details.
        reference (str): The reference identifier for the specific menu.

    Returns:
        Response: A Flask JSON response containing either the menu details or an error message.
        - On success: A JSON object with the following keys:
            - id: The ID of the menu.
            - name: The name of the menu.
            - reference: The reference identifier of the menu.
            - created: The creation timestamp of the menu.
            - user_with_access: The user associated with access to the menu.
        - On failure due to forbidden access: A JSON object with an "error" key and the message "Forbidden", along with a 403 status code.
    """

    jsonR = {'menu': []}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        sql = "SELECT * FROM menus WHERE reference = %s AND accountId = %s"
        queryVal = (reference, accountId,)
        mycursor.execute(sql, queryVal)
        menu = mycursor.fetchone()
        jsonR = {"id": menu[0], "name": menu[1], "reference": menu[3], "created": menu[2], "user_with_access": menu[4]}
    except Exception as e:
        print("get_menu_details model")
        print(e)
    finally:
        mydb.close()
        return jsonify(jsonR)


def get_menu_data(request, accountId: str, reference: str):
    """
    Get data for a single menu from the database.

    Args:
        request (Request): The HTTP request object.
        accountId (str): The account ID associated with the menu.
        reference (str): The reference code for the specific menu.

    Returns:
        dict: A JSON response containing data for the single menu. The response includes
        a menu of records ('data'), the total number of records ('recordsTotal'), and the
        number of records after filtering ('recordsFiltered') based on search criteria.
    """
    jsonR = {'data': [], 'recordsTotal': 0, 'recordsFiltered': 0}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        limit = int(request.args.get("iDisplayLength"))
        skip = int(request.args.get("iDisplayStart"))
        direction = request.args.get("sSortDir_0").upper()
        sortingColumn = request.args.get("iSortCol_0")

        if isinstance(int(accountId), int):
            tableName = f"account_{accountId}_menu_{reference}"
            add_reorder_column_if_not_exists(mycursor, mydb, tableName, "readingOrder", "INT(11)", False)
            # add_column_if_not_exists(mycursor, tableName, "readingOrder", "INT(11)", False)
            showColumnsQuery = f"SHOW COLUMNS FROM {tableName}"
            mycursor.execute(showColumnsQuery, )
            menuColumns = mycursor.fetchall()

            searchColumnsFields = []
            field_menu = []

            for columnIndex in range(len(menuColumns) - 1):
                search_value = request.args.get(f"sSearch_{columnIndex + 1}")
                if search_value:
                    searchColumnsFields.append({"field": menuColumns[columnIndex][0], "value": search_value.replace("((((", "").replace("))))", "")})

            for searchColumnsField in searchColumnsFields:
                searchColumnsFieldValue = searchColumnsField['value'].replace('"', "'")
                field_menu.append(f"{searchColumnsField['field']} LIKE %s")

            where_clause = " AND ".join(field_menu)
            if field_menu:
                query_params = list(f"%{searchColumnsField['value']}%" for searchColumnsField in searchColumnsFields)
                query = f"SELECT * FROM {tableName} WHERE {where_clause} ORDER BY {menuColumns[int(sortingColumn) - 1][0]} {direction} LIMIT %s, %s"
                mycursor.execute(query, query_params + [skip, limit])
            else:
                order_by = menuColumns[int(sortingColumn) - 1][0]
                query = f"SELECT * FROM {tableName} ORDER BY {order_by} {direction} LIMIT %s, %s"
                mycursor.execute(query, (skip, limit))

            menus = mycursor.fetchall()
            mycursor.execute(f"SELECT COUNT(*) FROM {tableName}")
            menuCount = mycursor.fetchone()[0]

            # Create json
            jsonR = {"data": menus, "recordsTotal": menuCount, "recordsFiltered": menuCount}

        else:
            print("Invalid accountId")

    except Exception as e:
        print("get_menu_data model")
        print(e)
    finally:
        mydb.close()
        return jsonify(jsonR)


def get_menu_columns(accountId: str, reference: str):
    """
    Get column information for a specific menu from the database.

    Args:
        accountId (str): The account ID associated with the menu.
        reference (str): The reference code for the specific menu.

    Returns:
        dict: A JSON response containing information about the columns of the specified menu.
    """
    jsonR = {'columns': []}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        if isinstance(int(accountId), int):
            tableName = f"account_{accountId}_menu_{reference}"

            # Create table if not exists
            create_table_query = f"CREATE TABLE IF NOT EXISTS {tableName} (id INT(11) AUTO_INCREMENT PRIMARY KEY UNIQUE, name VARCHAR(255))"
            mycursor.execute(create_table_query, )
            mydb.commit()

            # Retrieve column information
            show_columns_query = f"SHOW COLUMNS FROM {tableName}"
            mycursor.execute(show_columns_query, )
            columns_info = mycursor.fetchall()

            # Convert bytes to string for column names
            columns_info = [(item[0], item[1], item[2], item[3], item[4], item[5]) for item in columns_info]

            jsonR = {"columns": columns_info}
        else:
            print("Invalid accountId")

    except Exception as e:
        print("get_menu_columns model")
        print(e)
    finally:
        mydb.close()
        return jsonify(jsonR)


def get_menu_columns_with_returned_id(accountId: str, reference: str, fieldToReturn: str, linkedFieldToReturn: str, linkedFieldLabelToReturn: str):
    """
    Get column information for a specific menu from the database with additional information.

    Args:
        accountId (str): The account ID associated with the menu.
        reference (str): The reference code for the specific menu.
        fieldToReturn (str): The field to return.
        linkedFieldToReturn (str): The linked field to return.
        linkedFieldLabelToReturn (str): The linked field label to return.

    Returns:
        dict: A JSON response containing information about the columns of the specified menu,
        along with the specified fields to return.
    """
    jsonR = {'columns': [], 'fieldToReturn': fieldToReturn, 'linkedFieldToReturn': linkedFieldToReturn, 'linkedFieldLabelToReturn': linkedFieldLabelToReturn}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        tableName = f"account_{accountId}_menu_{reference}"

        # Create table if not exists
        create_table_query = "CREATE TABLE IF NOT EXISTS %s (id INT(11) AUTO_INCREMENT PRIMARY KEY UNIQUE, name VARCHAR(255))"
        mycursor.execute(create_table_query, (tableName,))
        mydb.commit()

        # Retrieve column information
        show_columns_query = "SHOW COLUMNS FROM %s"
        mycursor.execute(show_columns_query, (tableName,))
        columns_info = mycursor.fetchall()

        # Convert bytes to string for column names
        columns_info = [(item[0], item[1], item[2], item[3], item[4], item[5]) for item in columns_info]

        jsonR['columns'] = columns_info

    except Exception as e:
        print("get_menu_columns_with_returned_id model")
        print(e)
    finally:
        mydb.close()
        return jsonify(jsonR)


def get_menu_columns_with_properties(accountId: str, reference: str):
    """
    Get column properties for a specific menu from the database.

    Args:
        accountId (str): The account ID associated with the menu.
        reference (str): The reference code for the specific menu.

    Returns:
        dict: A JSON response containing properties for the columns of the specified menu.
    """
    jsonR = {'columns': []}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        tableName = f"account_{accountId}_menu_settings"

        if isinstance(int(accountId), int):
            # Retrieve column properties
            get_properties_query = f"SELECT * FROM {tableName} WHERE main_table = %s"
            mycursor.execute(get_properties_query, (reference,))
            columns_properties = mycursor.fetchall()

            jsonR['columns'] = columns_properties
        else:
            print("Invalid accountId")

    except Exception as e:
        print("get_menu_columns_with_properties model")
        print(e)
    finally:
        mydb.close()
        return jsonify(jsonR)


def get_menu_configuration(accountId: str, reference: str):
    """
    Get configuration information for a specific menu from the database.

    Args:
        accountId (str): The account ID associated with the menu.
        reference (str): The reference code for the specific menu.

    Returns:
        dict: A JSON response containing configuration information for the specified menu.
    """
    jsonR = {'columns': []}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    if isinstance(int(accountId), int):

        field_menu_for_config = ['id INT(11) AUTO_INCREMENT PRIMARY KEY UNIQUE',
                                 'main_table VARCHAR(255) DEFAULT NULL',
                                 'mandatory_fields VARCHAR(255) DEFAULT NULL',
                                 'save_by_field VARCHAR(11) DEFAULT 0',
                                 'field_to_save_by VARCHAR(255) DEFAULT NULL',
                                 'created_by INT(11) DEFAULT NULL',
                                 'modified_by INT(11) DEFAULT NULL',
                                 'created DATETIME NULL DEFAULT CURRENT_TIMESTAMP',
                                 'modified DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP']
        field_query_for_config = " (" + ", ".join(field_menu_for_config) + ")"

        tableName = f"account_{accountId}_menu_configuration"

        # Create table if not exists
        create_table_query = f"CREATE TABLE IF NOT EXISTS {tableName} {field_query_for_config}"
        mycursor.execute(create_table_query, )
        mydb.commit()

        # Retrieve configuration information
        get_config_query = f"SELECT * FROM {tableName} WHERE main_table = %s"
        mycursor.execute(get_config_query, (reference,))
        config_info = mycursor.fetchall()

        jsonR['columns'] = config_info
    else:
        print("Invalid accountId")

    return jsonify(jsonR)


def set_menu_configuration(request, accountId: str, reference: str):
    """
    Set configuration for a specific menu in the database.

    Args:
        request (Request): The HTTP request object.
        accountId (str): The account ID associated with the menu.
        reference (str): The reference code for the specific menu.

    Returns:
        menu: A menu containing the values that were inserted into the database for configuration.
    """
    col_to_return = []

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        tableName = f"account_{accountId}_menu_configuration"

        if isinstance(int(accountId), int):
            # Delete existing configuration for the specified menu
            delete_config_query = f"DELETE FROM {tableName} WHERE main_table = %s"
            mycursor.execute(delete_config_query, (reference,))
            mydb.commit()

            thisRequest = request.get_json()

            mfields = werkzeug.utils.escape(thisRequest.get("s-mandatory-fields"))
            modified_by = session["id"]

            if isinstance(mfields, list):
                mfields = ';'.join(mfields)

            col_to_return = [mfields, modified_by]

            # Insert new configuration for the specified menu
            insert_config_query = f"INSERT INTO {tableName} (main_table, mandatory_fields, created_by, modified_by) VALUES (%s, %s, %s, %s)"
            mycursor.execute(insert_config_query, (reference, mfields, modified_by, modified_by))
            mydb.commit()
        else:
            print("Invalid accountId")

    except Exception as e:
        print("set_menu_configuration model")
        print(e)
    finally:
        mydb.close()
        return jsonify(col_to_return)


def get_value_columns_with_index(accountId: str, reference: str, fieldToGet: str, fieldToLabel: str, indexToKeep: str, indexToKeepForAccountSettings: str):
    """
    Get columns with values and specified indices for a specific menu from the database.

    Args:
        accountId (str): The account ID associated with the menu.
        reference (str): The reference code for the specific menu.
        fieldToGet (str): The field from which to retrieve values.
        fieldToLabel (str): The field used as labels for the values.
        indexToKeep (str): The index to keep in the response.
        indexToKeepForAccountSettings (str): The index to keep for account settings.

    Returns:
        dict: A JSON response containing columns with values and specified indices for the specified menu.
    """
    jsonR = {'columns': [], "indexToKeep": indexToKeep, "indexToKeepForAccountSettings": indexToKeepForAccountSettings}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        tableName = f"account_{accountId}_menu_{reference}"

        if isinstance(int(accountId), int):
            # Retrieve columns with values and specified indices
            get_columns_query = f"SELECT %s, %s FROM {tableName}"
            mycursor.execute(get_columns_query, (fieldToGet, fieldToLabel))
            columns_data = mycursor.fetchall()

            jsonR = {"columns": columns_data, "indexToKeep": indexToKeep, "indexToKeepForAccountSettings": indexToKeepForAccountSettings}
        else:
            print("Invalid accountId")

    except Exception as e:
        print("get_value_columns_with_index model")
        print(e)
    finally:
        mydb.close()
        return jsonify(jsonR)


def upload_dynamic_menus(request):
    """
    Upload a dynamic menu from a CSV file.

    Args:
        request (Request): The HTTP request object.
    
    Returns:
        jsonify: A JSON response indicating the success of the upload.
    """
    toReturn = {}

    accountId = werkzeug.utils.escape(request.form.get("accountId"))

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    try:
        reference = werkzeug.utils.escape(request.form.get("reference"))
        uploaded_file = request.files['csv-file']

        if uploaded_file.filename != '':
            file_path = os.path.join(Config.TEMP_UPLOAD_FOLDER, uploaded_file.filename)
            uploaded_file.save(file_path)
            toReturn = parse_menu_csv(accountId, reference, file_path)

    except Exception as e:
        print("upload_dynamic_menus model")
        print(e)
    finally:
        return jsonify(toReturn)


def parse_menu_csv(accountId: str, reference: str, filePath: str):
    """
    Parse a CSV file and create/update a corresponding table in the database.

    Args:
        accountId (str): The account ID associated with the menu.
        reference (str): The reference code for the specific menu.
        filePath (str): The path to the CSV file.

    Returns:
        menu: A menu of column names in the created/updated table.

    Raises:
        Exception: An exception raised in case of any error during database operations.
    """

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        # Validate file existence
        if not os.path.isfile(filePath):
            raise FileNotFoundError(f"File not found: {filePath}")

        if isinstance(int(accountId), int):
            tableName = f"account_{accountId}_menu_{reference}"

            # Drop existing table if it exists
            mycursor.execute(f"DROP TABLE IF EXISTS {tableName}")
            mydb.commit()

            # Read CSV file using Pandas
            file = pd.read_csv(filePath, sep=",", encoding="utf-8", encoding_errors='ignore', engine="python", quoting=csv.QUOTE_ALL)

            # Get CSV column names
            col_names = file.columns.tolist()
            col_names_to_generate_fields = [field for field in col_names if field.strip().lower() != 'id']

            field_menu = ['id INT(11) AUTO_INCREMENT PRIMARY KEY UNIQUE']

            for field in col_names_to_generate_fields:
                field_menu.append(f'{field} LONGTEXT DEFAULT NULL')

            field_query = " (" + ", ".join(field_menu) + ")"

            # Create table if not exists
            create_table_query = f"CREATE TABLE IF NOT EXISTS {tableName}{field_query}"
            mycursor.execute(create_table_query, )
            mydb.commit()

            # Use Pandas to parse the CSV file
            csv_data = pd.read_csv(filePath, sep=",", encoding="utf-8", encoding_errors='ignore', engine="python", names=col_names, header=None)

            insert_query = f"INSERT INTO {tableName} ({', '.join(col_names)}) VALUES "

            # Loop through the rows
            for i, row in csv_data.iterrows():
                if i != 0:
                    values = map((lambda x: f'"' + html.escape(str((x if isinstance(x, float) else x.encode('utf-8'))).replace("\\", "__BACKSLASH__TO_REPLACE__")[2:-1]) + '"'), row)
                    joint_value = ', '.join(values)
                    mycursor.execute(f"{insert_query}({joint_value})")
                    mydb.commit()

                    if i + 1 == len(csv_data):
                        mydb.close()
                        return col_names
        else:
            print("Invalid accountId")

    except FileNotFoundError as e:
        print("parse_menu_csv model - 1")
        raise FileNotFoundError(f"File not found: {filePath}")
    except Exception as e:
        print("parse_menu_csv model - 2")
        raise RuntimeError(f"Error during CSV parsing and database update: {str(e)}")


def create_middle_tables(request, accountId: str, reference: str):
    """
    Create or update middle tables based on the form data.

    Args:
        request (Request): The HTTP request object.
        accountId (str): The account ID associated with the menu.
        reference (str): The reference code for the specific menu.
    """

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:

        if isinstance(int(accountId), int):
            # Define fields for the settings table
            field_menu_for_settings = ['id INT(11) AUTO_INCREMENT PRIMARY KEY UNIQUE']
            field_menu_for_settings.append("main_table VARCHAR(255) DEFAULT NULL")
            field_menu_for_settings.append("foreign_key VARCHAR(255) DEFAULT NULL")
            field_menu_for_settings.append("reference_table VARCHAR(255) DEFAULT NULL")
            field_menu_for_settings.append("assigned_field VARCHAR(255) DEFAULT NULL")
            field_menu_for_settings.append("assigned_field_label VARCHAR(255) DEFAULT NULL")
            field_menu_for_settings.append("field_type VARCHAR(255) DEFAULT NULL")
            field_menu_for_settings.append("start_visibility INT(11) DEFAULT NULL")
            field_query_for_settings = " (" + ", ".join(field_menu_for_settings) + ")"

            # Define the settings table name
            settings_table_name = f"account_{accountId}_menu_settings"

            # Create or update the settings table
            mycursor.execute(f"CREATE TABLE IF NOT EXISTS {settings_table_name}{field_query_for_settings}")
            mydb.commit()

            mycursor.execute(f"DELETE FROM {settings_table_name} WHERE main_table = '{reference}'")
            mydb.commit()

            # Iterate through form items
            for key, val in request.form.items():
                if key.startswith("selectItem"):
                    finalKey = str(key.replace("selectItem_", ""))
                    fieldToAssign = str(werkzeug.utils.escape(request.form.get(f"s-{finalKey}-assignedField")))
                    fieldToAssignLabel = str(werkzeug.utils.escape(request.form.get(f"s-{finalKey}-assignedFieldLabel")))
                    fieldToAssignType = str(werkzeug.utils.escape(request.form.get(f"typeSelectItem_{finalKey}")))
                    startVisibility = str(werkzeug.utils.escape(request.form.get(f"displaySettingsItem_{finalKey}")))

                    # Define the mapping table name
                    mapping_table_name = f"account_{accountId}_mappings_menu_{reference}_{val}"

                    # Drop existing mapping table
                    if val != "null":
                        mycursor.execute(f"DROP TABLE IF EXISTS {mapping_table_name}")
                        mydb.commit()

                        # Define fields for the mapping table
                        mapping_field_menu = ['id INT(11) AUTO_INCREMENT PRIMARY KEY UNIQUE']
                        mapping_field_menu.append(f"{reference}_id INT(11) DEFAULT NULL")
                        mapping_field_menu.append(f"{val}_id INT(11) DEFAULT NULL")
                        mapping_field_query = " (" + ", ".join(mapping_field_menu) + ")"

                        # Create the mapping table
                        mycursor.execute(f"CREATE TABLE IF NOT EXISTS {mapping_table_name}{mapping_field_query}")
                        mydb.commit()

                    # Insert or update settings table
                    if val != "null":
                        settings_query = (
                                "INSERT INTO "
                                + settings_table_name
                                + " (main_table, foreign_key, reference_table, assigned_field, assigned_field_label, field_type, start_visibility) "
                                + "VALUES (%s, %s, %s, %s, %s, %s, %s)"
                        )
                        mycursor.execute(settings_query, (reference, finalKey, val, fieldToAssign, fieldToAssignLabel, fieldToAssignType, startVisibility))
                    else:
                        settings_query = (
                                "INSERT INTO "
                                + settings_table_name
                                + " (main_table, foreign_key, reference_table, assigned_field, assigned_field_label, field_type, start_visibility) "
                                + "VALUES (%s, %s, %s, %s, %s, %s, %s)"
                        )
                        mycursor.execute(settings_query, (reference, finalKey, 'None', 'None', 'None', fieldToAssignType, startVisibility))

                    mydb.commit()
        else:
            print("Invalid accountId")

    except Exception as e:
        print("create_middle_tables model")
        print(e)
    finally:
        return "success"
        mydb.close()


def get_settings(accountId: str):
    """
    Get settings for a specific account from the database.

    Args:
        accountId (str): The account ID for which to retrieve settings.

    Returns:
        dict: A JSON response containing settings data.
    """
    json_response = {}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        if isinstance(int(accountId), int):
            field_menu_for_settings = [
                'id INT(11) AUTO_INCREMENT PRIMARY KEY UNIQUE',
                'main_table VARCHAR(255) DEFAULT NULL',
                'foreign_key VARCHAR(255) DEFAULT NULL',
                'reference_table VARCHAR(255) DEFAULT NULL',
                'assigned_field VARCHAR(255) DEFAULT NULL',
                'assigned_field_label VARCHAR(255) DEFAULT NULL',
                'field_type VARCHAR(255) DEFAULT NULL',
                'start_visibility INT(11) DEFAULT NULL'
            ]

            # Use a comma-separated string for field definitions
            field_query_for_settings = ", ".join(field_menu_for_settings)

            # Define the settings table name
            tableName = f"account_{accountId}_menu_settings"

            # Create or update the settings table
            # Since table names cannot be parameterized, use string formatting
            # Ensure you have sanitized `accountId` before this step
            create_table_query = f"CREATE TABLE IF NOT EXISTS {tableName} ({field_query_for_settings})"
            mycursor.execute(create_table_query)
            mydb.commit()

            # Retrieve settings from the table (avoid using '*' for security)
            select_query = f"SELECT id, main_table, foreign_key, reference_table, assigned_field, assigned_field_label, field_type, start_visibility FROM {tableName}"
            mycursor.execute(select_query, )
            settings_data = mycursor.fetchall()

            # Create JSON response
            json_response = {
                "settings": settings_data,
                "images_webpath": Config.IMAGES_WEBPATH,
                "original_images_webpath": Config.ORIGINAL_IMAGES_WEBPATH
            }
        else:
            print("Invalid accountId")

    except Exception as e:
        print("get_settings model")
        print(e)
    finally:
        mydb.close()
        return jsonify(json_response)


def get_all_menus(accountId: str):
    """
    Get a menu of all tables related to a specific account from the database.

    Args:
        accountId (str): The account ID for which to retrieve the menu of tables.

    Returns:
        dict: A JSON response containing a menu of tables related to the account.
    """
    json_response = {"menus": []}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        # Check for potential SQL injection by using parameterized queries
        query = "SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = %s AND TABLE_NAME REGEXP %s"
        mycursor.execute(query, (Config.DB_NAME, f'account_{accountId}_menu_'))

        # Fetch the results
        menus = mycursor.fetchall()

        # Create JSON response
        json_response = {"menus": menus}

    except Exception as e:
        print("get_all_menus model")
        print(e)
    finally:
        mydb.close()
        return jsonify(json_response)


def publish_dynamic_menus(request, account_menu: str, accountId: str, reference: str, env: str):
    """
    Publish dynamic menu data to JSON files and optionally by country.

    Args:
        request (Request): The HTTP request object.
        account_menu (str): The name of the database table.
        accountId (str): The account ID for which to retrieve the data.
        reference (str): The reference identifier.
        env (str): The environment identifier.

    Returns:
        Response: A JSON response containing the full menu data.
    """
    full_menu = []

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        # Query to retrieve all data from the specified database table (using parameterized query)
        mycursor.execute(f"SELECT * FROM {account_menu}")

        # Fetch column headers
        row_headers = [x[0] for x in mycursor.description]

        # Fetch all rows from the database table
        full_menu = mycursor.fetchall()

        # Convert data to a JSON format
        json_data = [dict(zip(row_headers, result)) for result in full_menu]
        json_data_to_write = json.dumps(json_data).replace('__BACKSLASH__TO_REPLACE__', '\\')

        # Write JSON data to a file with the specified reference identifier (sanitize reference)
        sanitized_reference = ''.join(e for e in reference if e.isalnum())
        with open(os.path.join(Config.WEBSERVER_FOLDER, Config.DYNAMIC_PATH, sanitized_reference + 'Menu.json'), 'w') as out_file:
            out_file.write(json_data_to_write)

    except Exception as e:
        print("publish_dynamic_menus model")
        print(e)
    finally:
        mydb.close()
        return jsonify({"full_menu": full_menu})


def update_dynamic_menus(request, accountId: str, account_menu: str):
    """
    Update a dynamic menu in the database.

    Args:
        request (Request): The HTTP request object containing the updated menu data.
        accountId (str): The Account ID.
        account_menu (str): The name of the database table containing the menu data.

    Returns:
        jsonify: JSON response containing the updated menu data.
    """
    json_response = {"menus": []}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    try:
        # Extract the menu item ID from the request
        this_request = request.get_json()
        item_id = werkzeug.utils.escape(this_request.get("e-id"))
        item_id = item_id.replace("e-", "")

        # Update the database with the new values
        columns_to_return = update_dynamic_menus_database(accountId, account_menu, item_id, this_request)

        # Return the updated menu data
        json_response = {"menus": columns_to_return}

    except Exception as e:
        print("update_dynamic_menus model")
        print(e)
    finally:
        return jsonify(json_response)


def update_dynamic_menus_database(accountId, account_menu, item_id, this_request):
    """
    Update the database with the new values.

    Args:
        accountId (str): The account ID for which to update the menus.
        account_menu (str): The name of the database table containing the menu data.
        item_id (str): The ID of the menu item to be updated.
        this_request (dict): The dictionary containing the updated menu data.

    Returns:
        menu: A menu of column names that were updated.
    """
    index = 0
    columns_to_return = []

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:

        if isinstance(int(accountId), int) and isinstance(int(item_id), int):
            for key, val in this_request.items():
                if key.startswith("e-"):
                    final_key = key.replace("e-", "")
                    columns_to_return.append(final_key)

                    if isinstance(val, list):
                        val = ';'.join(val)

                    # Update the database with the new value (use parameterized query to prevent SQL injection)
                    if final_key != 'id':
                        final_val = val.replace('"', "'")
                        mycursor.execute(f"UPDATE {account_menu} SET {final_key} = %s WHERE id = %s", (final_val, item_id))
                        mydb.commit()

                    index += 1

                    # Check if all columns are processed, then return the updated menu data
                    if (index == len(this_request)):
                        return columns_to_return
        else:
            print("Invalid accountId")

    except Exception as e:
        print("update_dynamic_menus_database model")
        print(f"Error updating dynamic menu: {str(e)}")
        return columns_to_return


def add_dynamic_menus(request, accountId: str, account_menu: str):
    """
    Add a dynamic menu to the database.

    Args:
        request (Request): The HTTP request object containing the data for the new menu entry.
        accountId (str): The Account ID.
        account_menu (str): The name of the database table to which the new menu entry will be added.

    Returns:
        jsonify: JSON response containing the added menu data.

    Raises:
        RuntimeError: An exception raised in case of any error during database operations.
    """

    json_response = {"menus": [], "lastEntry": False}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        # Extract data from the HTTP request
        this_request = request.get_json()

        # Get columns and values for the database query
        columns, column_values = prepare_columns_and_values_when_adding_menu(this_request, accountId)

        # Execute the database query
        last_row_id = execute_database_query_when_adding_menu(mydb, mycursor, accountId, account_menu, columns, column_values)

        # Update dynamically linked fields if necessary
        update_dynamically_linked_fields_when_adding_menu(mydb, mycursor, accountId, account_menu, this_request, last_row_id)

        # Return JSON response
        json_response = {"menus": columns, "lastEntry": last_row_id}

    except Exception as e:
        print("add_dynamic_menus model")
        print(e)
    finally:
        mydb.close()
        return jsonify(json_response)


def prepare_columns_and_values_when_adding_menu(this_request, accountId):
    """
    Prepare columns and values for the database query.

    Args:
        this_request (dict): The dictionary containing the data for the new menu entry.
        accountId (str): The account ID associated with the new menu.

    Returns:
        tuple: A tuple containing menus of columns and column values.
    """
    columns = []
    column_values = []

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    for key, val in this_request.items():
        if key.startswith("a-"):
            final_key = key.replace("a-", "")

            if isinstance(val, list):
                val = ';'.join(val)

            if final_key.strip() != 'id':
                columns.append(final_key)
                column_values.append(val)

    return columns, column_values


def execute_database_query_when_adding_menu(mydb, mycursor, accountId, account_menu, columns, column_values):
    """
    Execute the database query to add a new menu entry.

    Args:
        mydb: The MySQL database connection object.
        mycursor: The MySQL cursor object.
        accountId (str): The account ID associated with the menu.
        account_menu (str): The name of the database table to which the new menu entry will be added.
        columns (menu): A menu of column names.
        column_values (menu): A menu of column values.

    Returns:
        str: The ID of the last inserted row.
    """

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    columns_for_query = " (" + ", ".join(columns) + ")"
    column_values_for_query = " ('" + "', '".join(column_values) + "')"

    mycursor.execute(f"INSERT INTO {account_menu}{columns_for_query} VALUES{column_values_for_query}")
    mydb.commit()

    return str(mycursor.lastrowid)


def update_dynamically_linked_fields_when_adding_menu(mydb, mycursor, accountId, account_menu, this_request, last_row_id):
    """
    Update dynamically linked fields if necessary.

    Args:
        mydb: The MySQL database connection object.
        mycursor: The MySQL cursor object.
        accountId (str): The account ID associated with the dynamic linked fields.
        account_menu (str): The name of the database table.
        this_request (dict): The dictionary containing the data for the new menu entry.
        last_row_id (str): The ID of the last inserted row.
    """

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    final_key_to_update_dynamically = ''
    final_val_to_update_dynamically = ''

    for key, val in this_request.items():
        if key.startswith("a-"):
            final_key = key.replace("a-", "")

            if final_key.strip().lower().endswith("id"):
                final_key_to_update_dynamically = final_key
                final_val_to_update_dynamically = val + last_row_id

    if final_key_to_update_dynamically:
        mycursor.execute(f"UPDATE {account_menu} SET {final_key_to_update_dynamically} = {final_val_to_update_dynamically} WHERE id = '{last_row_id}'")
        mydb.commit()


def delete_dynamic_menus(request, accountId: str, account_menu: str):
    """
    Delete selected entries from a dynamic menu in the database.

    Args:
        request (Request): The HTTP request object containing the IDs of the entries to be deleted.
        accountId (str): The Account ID.
        account_menu (str): The name of the database table from which entries will be deleted.

    Returns:
        jsonify: JSON response containing the remaining menus after deletion.
    """

    json_response = {"menus": []}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        # Extract data from the HTTP request
        entries_to_delete = werkzeug.utils.escape(request.form.get("entries_to_delete"))

        # Validate entries_to_delete to prevent SQL injection
        validate_entries_to_delete(entries_to_delete, accountId)

        # Delete selected entries from the database
        mycursor.execute(f"DELETE FROM {account_menu} WHERE id IN ({entries_to_delete})")
        mydb.commit()

        # Retrieve the updated menu of tables after deletion
        mycursor.execute(f"SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA=%s AND TABLE_NAME REGEXP %s", (Config.DB_NAME, account_menu,))
        menus = mycursor.fetchall()

        json_response = {"menus": menus}

    except Exception as e:
        print("delete_dynamic_menus model")
        print(e)
    finally:
        mydb.close()
        return jsonify(json_response)


def validate_entries_to_delete(entries_to_delete, accountId):
    """
    Validate the entries_to_delete parameter to prevent SQL injection.

    Args:
        entries_to_delete (str): The string containing IDs of entries to be deleted.
        accountId (str): The account ID associated with the entries to delete.

    Raises:
        ValueError: If entries_to_delete contains invalid characters.
    """

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    if not entries_to_delete.isdigit() or ";" in entries_to_delete:
        print("validate_entries_to_delete model")
        raise ValueError("Invalid entries_to_delete parameter.")


def add_single_menu(request):
    """
    Add a new menu to the database.

    Args:
        request (Request): The HTTP request object containing data for the new menu.

    Returns:
        jsonify: JSON response containing the details of the added menu.
    """
    last_row = {}

    accountId = werkzeug.utils.escape(request.form.get("accountId"))

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        # Extract data from the HTTP request
        name = werkzeug.utils.escape(request.form.get("name"))
        reference = werkzeug.utils.escape(request.form.get("reference"))

        # Validate input data
        validate_input_data_to_add(name, reference, accountId)

        # Insert new menu into the 'menus' table
        insert_query = "INSERT INTO menus (name, reference, accountId) VALUES (%s, %s, %s)"
        mycursor.execute(insert_query, (name, reference, accountId))
        mydb.commit()

        # Retrieve the details of the added menu
        select_query = "SELECT * FROM menus WHERE accountId = %s AND reference = %s"
        mycursor.execute(select_query, (accountId, reference))
        last_row = mycursor.fetchone()

    except Exception as e:
        print("add_single_menu model")
        print(e)
    finally:
        mydb.close()
        # Return JSON response containing the details of the added menu
        return jsonify(last_row)


def validate_input_data_to_add(name, reference, accountId):
    """
    Validate input data to prevent SQL injection.

    Args:
        name (str): The name of the new menu.
        reference (str): The reference code for the new menu.
        accountId (str): The account ID associated with the new menu.

    Raises:
        ValueError: If any input data is invalid.
    """

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    if not (name and reference and accountId.isdigit()):
        print("validate_input_data_to_add model")
        raise ValueError("Invalid input data for adding a new menu.")


def update_single_menu(request):
    """
    Update a menu in the database.

    Args:
        request (Request): The HTTP request object containing data for the menu update.

    Returns:
        jsonify: JSON response containing the details of the updated menu.
    """
    json_response = {}

    accountId = werkzeug.utils.escape(request.form.get("accountId"))

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    try:
        reference = werkzeug.utils.escape(request.form.get("reference"))
        original_menu_name = werkzeug.utils.escape(request.form.get("original_menu_name"))
        new_menu_name = werkzeug.utils.escape(request.form.get("new_menu_name"))
        user_with_access = werkzeug.utils.escape(request.form.get("user_with_access"))

        # Validate input data
        validate_input_data_to_update(reference, accountId, original_menu_name, new_menu_name, user_with_access)

        # Connect to the database
        with db_connection() as (mydb, mycursor):
            # Update the menu in the 'menus' table
            update_query = "UPDATE menus SET name=%s, reference=%s, user_with_access=%s WHERE name=%s AND accountId=%s"
            values = (new_menu_name, reference, user_with_access, original_menu_name, accountId)
            mycursor.execute(update_query, values)
            mydb.commit()

            json_response = {"name": new_menu_name, "reference": reference}

    except Exception as e:
        print("update_single_menu model")
        print(e)
    finally:
        if mydb:
            return jsonify(json_response)


def validate_input_data_to_update(reference, accountId, original_menu_name, new_menu_name, user_with_access):
    """
    Validate input data to prevent SQL injection.

    Args:
        reference (str): The reference code for the menu.
        accountId (str): The account ID associated with the menu.
        original_menu_name (str): The original name of the menu.
        new_menu_name (str): The new name for the menu.
        user_with_access (str): User with access to the menu.

    Raises:
        ValueError: If any input data is invalid.
    """

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    if not all((reference, accountId.isdigit(), original_menu_name, new_menu_name, user_with_access)):
        print("validate_input_data_to_update model")
        raise ValueError("Invalid input data for updating a menu.")


def delete_multiple_menus(request):
    """
    Delete multiple menus from the database.

    Args:
        request (Request): The HTTP request object containing data for the menus deletion.

    Returns:
        jsonify: JSON response containing information about the deleted menus.
    """
    json_response = {}

    accountId = werkzeug.utils.escape(request.form.get("accountId"))

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    try:
        menus_to_delete = werkzeug.utils.escape(request.form.get("menus_to_delete"))

        if not menus_to_delete:
            json_response = {"menus_to_delete": "None provided", "action": "none"}
            return jsonify(json_response)

        # Convert the string to a menu
        menus_to_delete = [menu_name.strip() for menu_name in menus_to_delete.split(",")]

        # Connect to the database
        with db_connection() as (mydb, mycursor):
            # Delete rows from the 'menus' table
            delete_query = "DELETE FROM menus WHERE name IN (%s) AND accountId=%s"
            values = (",".join(["%s"] * len(menus_to_delete)), accountId, *menus_to_delete)
            mycursor.execute(delete_query, values)
            mydb.commit()

            # Drop corresponding tables
            for menu_name in menus_to_delete:
                # Validate input data
                validate_input_data_to_delete(menu_name, accountId)

                table_name = f"account_{accountId}_menu_{menu_name}"
                mycursor.execute(f"DROP TABLE IF EXISTS %s", (table_name,))
                mydb.commit()

            json_response = {"menus_to_delete": menus_to_delete, "action": "deleted"}

    except Exception as e:
        print("delete_multiple_menus model")
        print(e)
    finally:
        return jsonify(json_response)


def delete_single_menu(request):
    """
    Delete a menu from the database.

    Args:
        request (Request): The HTTP request object containing data for the menu deletion.

    Returns:
        jsonify: JSON response containing information about the deleted menu.

    Raises:
        RuntimeError: An exception raised in case of any error during database operations.
    """
    json_response = {}

    accountId = werkzeug.utils.escape(request.form.get("accountId"))

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    try:
        name = werkzeug.utils.escape(request.form.get("name"))

        # Validate input data
        validate_input_data_to_delete(name, accountId)

        # Connect to the database
        with db_connection() as (mydb, mycursor):
            # Delete row from the 'menus' table
            delete_query = "DELETE FROM menus WHERE name=%s AND accountId=%s"
            values = (name, accountId)
            mycursor.execute(delete_query, values)
            mydb.commit()

            json_response = {"name": name, "action": "deleted"}

    except Exception as e:
        print("delete_single_menu model")
        print(e)
    finally:
        mydb.close()
        return jsonify(json_response)


def reorder_menu_items(request, accountId: str, reference: str):
    jsonR = {'updated': False}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:

        data = request.get_json()

        if isinstance(int(accountId), int):

            tableName = f"account_{accountId}_menu_{reference}"

            for single_entry in data:
                new_id = int(single_entry["newPosition"] + 1)
                item_id = int(single_entry["oldData"])  # Use the temporary unique value
                # Update the temporary value to the new position
                mycursor.execute(f"UPDATE {tableName} SET readingOrder = %s WHERE id = %s", (new_id, item_id))
                mydb.commit()

            # Create json response
            jsonR = {"updated": True}
            return jsonify(jsonR), 200

        else:
            print("Invalid accountId")

    except Exception as e:
        print("reorder_menu_items model")
        print(e)
    finally:
        mydb.close()
        return jsonify(jsonR)

def add_reorder_column_if_not_exists(cursor, db_connection, table_name, column_name, column_definition, after_column):
    try:
        # Check if the column exists
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{table_name}' AND COLUMN_NAME = '{column_name}'
        """)
        column_exists = cursor.fetchone()[0] > 0

        if not column_exists:
            # Column does not exist, so add it
            if after_column:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition} AFTER {after_column}")
            else:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")

            if column_name == "readingOrder":
                # Populate the new column with incremented values
                cursor.execute("SET @row_number = 0;")
                cursor.execute(f"UPDATE {table_name} SET {column_name} = (@row_number := @row_number + 1);")
        else:
            if column_name == "readingOrder":
                # Ensure the column is not NULL and has incremented values
                cursor.execute("SET @row_number = 0;")
                cursor.execute(f"""
                    UPDATE {table_name}
                    SET {column_name} = COALESCE({column_name}, (@row_number := @row_number + 1))
                    ORDER BY id;
                """)

        # Commit the changes to the database
        db_connection.commit()
    except Exception as e:
        print("add_reorder_column_if_not_exists model")
        print(e)

def validate_input_data_to_delete(menu_to_delete, accountId):
    """
    Validate input data to prevent SQL injection.

    Args:
        menu_to_delete (str): Comma-separated menu of menus to delete.
        accountId (str): The account ID associated with the menus.

    Raises:
        ValueError: If any input data is invalid.
    """

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    if not all((menu_to_delete, accountId.isdigit())):
        print("validate_input_data_to_delete model")
        raise ValueError("Invalid input data for deleting menu.")


def menu_belongs_to_account(menu_id):
    """
    Check if the specified menu ID belongs to the specified account ID.

    Args:
        menu_id (int): The ID of the menu to check.

    Returns:
        bool: True if the site belongs to the account, False otherwise.
    """

    try:
        accountId = session["accountId"]
        mydb, mycursor = db_connection()

        # Check if the site ID belongs to the specified account
        mycursor.execute("SELECT COUNT(*) FROM menus WHERE id = %s AND accountId = %s", (menu_id, accountId))
        result = mycursor.fetchone()

        # If there is at least one matching record, the site belongs to the account
        return result[0] > 0

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        print(f"An error occurred: {str(e)}")
        return False
