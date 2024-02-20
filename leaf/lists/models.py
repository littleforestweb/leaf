# models.py
import re

from flask import jsonify, session, current_app
from leaf.decorators import db_connection
from leaf.config import Config
import pandas as pd
import csv
import os
import html
import json
import werkzeug.utils


def get_lists_data(accountId: int, userId: str, isAdmin: str):
    """
    Get lists data from the database.

    Args:
        accountId (int): The account ID for which to retrieve lists data.
        isAdmin (str): A string indicating whether the user is an administrator (1 for admin, 0 for non-admin).

    Returns:
        dict: A JSON response containing lists data. The response includes a list of dictionaries, each
        representing a list with keys 'id', 'name', 'reference', 'created', and 'user_with_access'.
    """
    jsonR = {'lists': []}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        if isAdmin != '1':
            sql = "SELECT lists.id, lists.name, lists.reference, lists.created, lists.user_with_access FROM lists WHERE (accountId = %s AND LOCATE('userId', user_with_access) > 0) OR (accountId = %s AND lists.name = 'Articles') OR (accountId = %s AND lists.name = 'News') OR (accountId = %s AND lists.name = 'People')"
            queryVal = (accountId, accountId, accountId, accountId)
            mycursor.execute(sql, queryVal)
        else:
            sql = "SELECT lists.id, lists.name, lists.reference, lists.created, lists.user_with_access FROM lists WHERE accountId = %s"
            queryVal = (accountId,)
            mycursor.execute(sql, queryVal)

        lists = mycursor.fetchall()

        listsLst = [{"id": singleList[0], "name": singleList[1], "reference": singleList[3], "created": singleList[2], "user_with_access": singleList[4]} for singleList in lists]

        jsonR = {"lists": listsLst}

    except Exception as e:
        print("get_lists_data model")
        print(e)
    finally:
        mydb.close()
        return jsonify(jsonR)


def get_list_data(request, accountId: str, reference: str):
    """
    Get data for a single list from the database.

    Args:
        request (Request): The HTTP request object.
        accountId (str): The account ID associated with the list.
        reference (str): The reference code for the specific list.

    Returns:
        dict: A JSON response containing data for the single list. The response includes
        a list of records ('data'), the total number of records ('recordsTotal'), and the
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
            tableName = f"account_{accountId}_list_{reference}"
            showColumnsQuery = f"SHOW COLUMNS FROM {tableName}"
            mycursor.execute(showColumnsQuery, )
            listColumns = mycursor.fetchall()

            searchColumnsFields = []
            field_list = []

            for columnIndex in range(len(listColumns) - 1):
                search_value = request.args.get(f"sSearch_{columnIndex + 1}")
                if search_value:
                    searchColumnsFields.append({"field": listColumns[columnIndex][0], "value": search_value.replace("((((", "").replace("))))", "")})

            for searchColumnsField in searchColumnsFields:
                searchColumnsFieldValue = searchColumnsField['value'].replace('"', "'")
                field_list.append(f"{searchColumnsField['field']} LIKE %s")

            where_clause = " AND ".join(field_list)
            if field_list:
                query_params = list(f"%{searchColumnsField['value']}%" for searchColumnsField in searchColumnsFields)
                query = f"SELECT * FROM {tableName} WHERE {where_clause} ORDER BY {listColumns[int(sortingColumn) - 1][0]} {direction} LIMIT %s, %s"
                mycursor.execute(query, query_params + [skip, limit])
            else:
                order_by = listColumns[int(sortingColumn) - 1][0]
                query = f"SELECT * FROM {tableName} ORDER BY {order_by} {direction} LIMIT %s, %s"
                mycursor.execute(query, (skip, limit))

            lists = mycursor.fetchall()

            mycursor.execute(f"SELECT COUNT(*) FROM {tableName}")
            listCount = mycursor.fetchone()[0]

            # Create json
            jsonR = {"data": lists, "recordsTotal": listCount, "recordsFiltered": listCount}

        else:
            print("Invalid accountId")

    except Exception as e:
        print("get_list_data model")
        print(e)
    finally:
        mydb.close()
        return jsonify(jsonR)


def get_list_columns(accountId: str, reference: str):
    """
    Get column information for a specific list from the database.

    Args:
        accountId (str): The account ID associated with the list.
        reference (str): The reference code for the specific list.

    Returns:
        dict: A JSON response containing information about the columns of the specified list.
    """
    jsonR = {'columns': []}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        if isinstance(int(accountId), int):
            tableName = f"account_{accountId}_list_{reference}"

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
        print("get_list_columns model")
        print(e)
    finally:
        mydb.close()
        return jsonify(jsonR)


def get_list_columns_with_returned_id(accountId: str, reference: str, fieldToReturn: str, linkedFieldToReturn: str, linkedFieldLabelToReturn: str):
    """
    Get column information for a specific list from the database with additional information.

    Args:
        accountId (str): The account ID associated with the list.
        reference (str): The reference code for the specific list.
        fieldToReturn (str): The field to return.
        linkedFieldToReturn (str): The linked field to return.
        linkedFieldLabelToReturn (str): The linked field label to return.

    Returns:
        dict: A JSON response containing information about the columns of the specified list,
        along with the specified fields to return.
    """
    jsonR = {'columns': [], 'fieldToReturn': fieldToReturn, 'linkedFieldToReturn': linkedFieldToReturn, 'linkedFieldLabelToReturn': linkedFieldLabelToReturn}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        tableName = f"account_{accountId}_list_{reference}"

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
        print("get_list_columns_with_returned_id model")
        print(e)
    finally:
        mydb.close()
        return jsonify(jsonR)


def get_list_columns_with_properties(accountId: str, reference: str):
    """
    Get column properties for a specific list from the database.

    Args:
        accountId (str): The account ID associated with the list.
        reference (str): The reference code for the specific list.

    Returns:
        dict: A JSON response containing properties for the columns of the specified list.
    """
    jsonR = {'columns': []}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        tableName = f"account_{accountId}_list_settings"

        if isinstance(int(accountId), int):
            # Retrieve column properties
            get_properties_query = f"SELECT * FROM {tableName} WHERE main_table = %s"
            mycursor.execute(get_properties_query, (reference,))
            columns_properties = mycursor.fetchall()

            jsonR['columns'] = columns_properties
        else:
            print("Invalid accountId")

    except Exception as e:
        print("get_list_columns_with_properties model")
        print(e)
    finally:
        mydb.close()
        return jsonify(jsonR)


def get_list_configuration(accountId: str, reference: str):
    """
    Get configuration information for a specific list from the database.

    Args:
        accountId (str): The account ID associated with the list.
        reference (str): The reference code for the specific list.

    Returns:
        dict: A JSON response containing configuration information for the specified list.
    """
    jsonR = {'columns': []}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    if isinstance(int(accountId), int):

        field_list_for_config = ['id INT(11) AUTO_INCREMENT PRIMARY KEY UNIQUE',
                                 'main_table VARCHAR(255) DEFAULT NULL',
                                 'template VARCHAR(255) DEFAULT NULL',
                                 'parameters VARCHAR(255) DEFAULT NULL',
                                 'fields VARCHAR(255) DEFAULT NULL',
                                 'mandatory_fields VARCHAR(255) DEFAULT NULL',
                                 'save_by_field VARCHAR(11) DEFAULT 0',
                                 'field_to_save_by VARCHAR(255) DEFAULT NULL']
        field_query_for_config = " (" + ", ".join(field_list_for_config) + ")"

        tableName = f"account_{accountId}_list_configuration"

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


def set_list_configuration(request, accountId: str, reference: str):
    """
    Set configuration for a specific list in the database.

    Args:
        request (Request): The HTTP request object.
        accountId (str): The account ID associated with the list.
        reference (str): The reference code for the specific list.

    Returns:
        list: A list containing the values that were inserted into the database for configuration.
    """
    col_to_return = []

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        tableName = f"account_{accountId}_list_configuration"

        if isinstance(int(accountId), int):
            # Delete existing configuration for the specified list
            delete_config_query = f"DELETE FROM {tableName} WHERE main_table = %s"
            mycursor.execute(delete_config_query, (reference,))
            mydb.commit()

            thisRequest = request.get_json()

            template = werkzeug.utils.escape(str(thisRequest.get("s-template")))
            parameters = werkzeug.utils.escape(str(thisRequest.get("s-parameters")))
            fields = werkzeug.utils.escape(thisRequest.get("s-fields"))
            mfields = werkzeug.utils.escape(thisRequest.get("s-mandatory-fields"))
            save_by_field = werkzeug.utils.escape(thisRequest.get("s-save-by-field"))
            field_to_save_by = werkzeug.utils.escape(thisRequest.get("s-field-to-save-by"))

            # Convert lists to strings for storage
            if isinstance(fields, list):
                fields = ';'.join(fields)

            if isinstance(mfields, list):
                mfields = ';'.join(mfields)

            if isinstance(field_to_save_by, list):
                field_to_save_by = ';'.join(field_to_save_by)

            col_to_return = [template, parameters, fields, mfields, save_by_field, field_to_save_by]

            # Insert new configuration for the specified list
            insert_config_query = f"INSERT INTO {tableName} (main_table, template, parameters, fields, mandatory_fields, save_by_field, field_to_save_by) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            mycursor.execute(insert_config_query, (reference, template, parameters, fields, mfields, save_by_field, field_to_save_by))
            mydb.commit()
        else:
            print("Invalid accountId")

    except Exception as e:
        print("set_list_configuration model")
        print(e)
    finally:
        mydb.close()
        return jsonify(col_to_return)


def get_value_columns_with_index(accountId: str, reference: str, fieldToGet: str, fieldToLabel: str, indexToKeep: str, indexToKeepForAccountSettings: str):
    """
    Get columns with values and specified indices for a specific list from the database.

    Args:
        accountId (str): The account ID associated with the list.
        reference (str): The reference code for the specific list.
        fieldToGet (str): The field from which to retrieve values.
        fieldToLabel (str): The field used as labels for the values.
        indexToKeep (str): The index to keep in the response.
        indexToKeepForAccountSettings (str): The index to keep for account settings.

    Returns:
        dict: A JSON response containing columns with values and specified indices for the specified list.
    """
    jsonR = {'columns': [], "indexToKeep": indexToKeep, "indexToKeepForAccountSettings": indexToKeepForAccountSettings}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        tableName = f"account_{accountId}_list_{reference}"

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


def upload_dynamic_lists(request):
    """
    Upload a dynamic list from a CSV file.

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
            toReturn = parse_csv(accountId, reference, file_path)

    except Exception as e:
        print("upload_dynamic_lists model")
        print(e)
    finally:
        return jsonify(toReturn)


def parse_csv(accountId: str, reference: str, filePath: str):
    """
    Parse a CSV file and create/update a corresponding table in the database.

    Args:
        accountId (str): The account ID associated with the list.
        reference (str): The reference code for the specific list.
        filePath (str): The path to the CSV file.

    Returns:
        list: A list of column names in the created/updated table.

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
            tableName = f"account_{accountId}_list_{reference}"

            # Drop existing table if it exists
            mycursor.execute(f"DROP TABLE IF EXISTS {tableName}")
            mydb.commit()

            # Read CSV file using Pandas
            file = pd.read_csv(filePath, sep=",", encoding="utf-8", encoding_errors='ignore', engine="python", quoting=csv.QUOTE_ALL)

            # Get CSV column names
            col_names = file.columns.tolist()
            col_names_to_generate_fields = [field for field in col_names if field.strip().lower() != 'id']

            field_list = ['id INT(11) AUTO_INCREMENT PRIMARY KEY UNIQUE']

            for field in col_names_to_generate_fields:
                field_list.append(f'{field} LONGTEXT DEFAULT NULL')

            field_query = " (" + ", ".join(field_list) + ")"

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
        print("parse_csv model - 1")
        raise FileNotFoundError(f"File not found: {filePath}")
    except Exception as e:
        print("parse_csv model - 2")
        raise RuntimeError(f"Error during CSV parsing and database update: {str(e)}")


def create_middle_tables(request, accountId: str, reference: str):
    """
    Create or update middle tables based on the form data.

    Args:
        request (Request): The HTTP request object.
        accountId (str): The account ID associated with the list.
        reference (str): The reference code for the specific list.
    """

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:

        if isinstance(int(accountId), int):
            # Define fields for the settings table
            field_list_for_settings = ['id INT(11) AUTO_INCREMENT PRIMARY KEY UNIQUE']
            field_list_for_settings.append("main_table VARCHAR(255) DEFAULT NULL")
            field_list_for_settings.append("foreign_key VARCHAR(255) DEFAULT NULL")
            field_list_for_settings.append("reference_table VARCHAR(255) DEFAULT NULL")
            field_list_for_settings.append("assigned_field VARCHAR(255) DEFAULT NULL")
            field_list_for_settings.append("assigned_field_label VARCHAR(255) DEFAULT NULL")
            field_list_for_settings.append("field_type VARCHAR(255) DEFAULT NULL")
            field_list_for_settings.append("start_visibility INT(11) DEFAULT NULL")
            field_query_for_settings = " (" + ", ".join(field_list_for_settings) + ")"

            # Define the settings table name
            settings_table_name = f"account_{accountId}_list_settings"

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
                    mapping_table_name = f"account_{accountId}_mappings_list_{reference}_{val}"

                    # Drop existing mapping table
                    if val != "null":
                        mycursor.execute(f"DROP TABLE IF EXISTS {mapping_table_name}")
                        mydb.commit()

                        # Define fields for the mapping table
                        mapping_field_list = ['id INT(11) AUTO_INCREMENT PRIMARY KEY UNIQUE']
                        mapping_field_list.append(f"{reference}_id INT(11) DEFAULT NULL")
                        mapping_field_list.append(f"{val}_id INT(11) DEFAULT NULL")
                        mapping_field_query = " (" + ", ".join(mapping_field_list) + ")"

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
            field_list_for_settings = [
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
            field_query_for_settings = ", ".join(field_list_for_settings)

            # Define the settings table name
            tableName = f"account_{accountId}_list_settings"

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


def get_all_lists(accountId: str):
    """
    Get a list of all tables related to a specific account from the database.

    Args:
        accountId (str): The account ID for which to retrieve the list of tables.

    Returns:
        dict: A JSON response containing a list of tables related to the account.
    """
    json_response = {"lists": []}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        # Check for potential SQL injection by using parameterized queries
        query = "SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = %s AND TABLE_NAME REGEXP %s"
        mycursor.execute(query, (Config.DB_NAME, f'account_{accountId}_list_'))

        # Fetch the results
        lists = mycursor.fetchall()

        # Create JSON response
        json_response = {"lists": lists}

    except Exception as e:
        print("get_all_lists model")
        print(e)
    finally:
        mydb.close()
        return jsonify(json_response)


def publish_dynamic_lists(request, account_list: str, accountId: str, reference: str, env: str):
    """
    Publish dynamic list data to JSON files and optionally by country.

    Args:
        request (Request): The HTTP request object.
        account_list (str): The name of the database table.
        accountId (str): The account ID for which to retrieve the data.
        reference (str): The reference identifier.
        env (str): The environment identifier.

    Returns:
        Response: A JSON response containing the full list data.
    """
    full_list = []

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        # Query to retrieve all data from the specified database table (using parameterized query)
        mycursor.execute(f"SELECT * FROM {account_list}")

        # Fetch column headers
        row_headers = [x[0] for x in mycursor.description]

        # Fetch all rows from the database table
        full_list = mycursor.fetchall()

        # Convert data to a JSON format
        json_data = [dict(zip(row_headers, result)) for result in full_list]
        json_data_to_write = json.dumps(json_data).replace('__BACKSLASH__TO_REPLACE__', '\\')

        # Write JSON data to a file with the specified reference identifier (sanitize reference)
        sanitized_reference = ''.join(e for e in reference if e.isalnum())
        with open(os.path.join(Config.DYNAMIC_PATH, sanitized_reference + 'List.json'), 'w') as out_file:
            out_file.write(json_data_to_write)

        # Additional logic to save data by country (sanitize user input)
        this_request = request.get_json()
        country_to_update = werkzeug.utils.escape(this_request.get("country_to_update"))
        if country_to_update and isinstance(country_to_update, list):
            country_to_update = ';'.join(country_to_update)

            single_country_to_update = country_to_update.split(';')
            for single_country_to_update in single_country_to_update:
                # Query to retrieve data filtered by country (using parameterized query)
                mycursor.execute(f"SELECT * FROM {account_list} WHERE LOWER(`country`) LIKE %s",
                                 ('%' + single_country_to_update.strip().lower() + '%',))
                row_headers = [x[0] for x in mycursor.description]
                full_list_by_country = mycursor.fetchall()

                # Convert data to a JSON format
                json_data_by_country = [dict(zip(row_headers, result)) for result in full_list_by_country]
                json_data_to_write_by_country = json.dumps(json_data_by_country).replace('__BACKSLASH__TO_REPLACE__', '\\')

                # Write JSON data to a file with the country-specific reference identifier (sanitize reference)
                sanitized_reference_by_country = ''.join(e for e in sanitized_reference + '_' + single_country_to_update.strip().lower() if e.isalnum())
                with open(os.path.join(Config.DYNAMIC_PATH, 'json_by_country', sanitized_reference_by_country + '_List.json'), 'w') as out_file_by_country:
                    out_file_by_country.write(json_data_to_write_by_country)

    except Exception as e:
        print("publish_dynamic_lists model")
        print(e)
    finally:
        mydb.close()
        return jsonify({"full_list": full_list})


def update_dynamic_lists(request, accountId: str, account_list: str):
    """
    Update a dynamic list in the database.

    Args:
        request (Request): The HTTP request object containing the updated list data.
        accountId (str): The Account ID.
        account_list (str): The name of the database table containing the list data.

    Returns:
        jsonify: JSON response containing the updated list data.
    """
    json_response = {"lists": []}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    try:
        # Extract the list item ID from the request
        this_request = request.get_json()
        item_id = werkzeug.utils.escape(this_request.get("e-id"))
        item_id = item_id.replace("e-", "")

        # Update the database with the new values
        columns_to_return = update_dynamic_lists_database(accountId, account_list, item_id, this_request)

        # Return the updated list data
        json_response = {"lists": columns_to_return}

    except Exception as e:
        print("update_dynamic_lists model")
        print(e)
    finally:
        return jsonify(json_response)


def update_dynamic_lists_database(accountId, account_list, item_id, this_request):
    """
    Update the database with the new values.

    Args:
        accountId (str): The account ID for which to update the lists.
        account_list (str): The name of the database table containing the list data.
        item_id (str): The ID of the list item to be updated.
        this_request (dict): The dictionary containing the updated list data.

    Returns:
        list: A list of column names that were updated.
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
                        mycursor.execute(f"UPDATE {account_list} SET {final_key} = %s WHERE id = %s", (final_val, item_id))
                        mydb.commit()

                    index += 1

                    # Check if all columns are processed, then return the updated list data
                    if (index == len(this_request)):
                        return columns_to_return
        else:
            print("Invalid accountId")

    except Exception as e:
        print("update_dynamic_lists_database model")
        print(f"Error updating dynamic list: {str(e)}")
        return columns_to_return


def add_dynamic_lists(request, accountId: str, account_list: str):
    """
    Add a dynamic list to the database.

    Args:
        request (Request): The HTTP request object containing the data for the new list entry.
        accountId (str): The Account ID.
        account_list (str): The name of the database table to which the new list entry will be added.

    Returns:
        jsonify: JSON response containing the added list data.

    Raises:
        RuntimeError: An exception raised in case of any error during database operations.
    """

    json_response = {"lists": [], "lastEntry": False}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        # Extract data from the HTTP request
        this_request = request.get_json()

        # Get columns and values for the database query
        columns, column_values = prepare_columns_and_values_when_adding_list(this_request, accountId)

        # Execute the database query
        last_row_id = execute_database_query_when_adding_list(mydb, mycursor, accountId, account_list, columns, column_values)

        # Update dynamically linked fields if necessary
        update_dynamically_linked_fields_when_adding_list(mydb, mycursor, accountId, account_list, this_request, last_row_id)

        # Return JSON response
        json_response = {"lists": columns, "lastEntry": last_row_id}

    except Exception as e:
        print("add_dynamic_lists model")
        print(e)
    finally:
        mydb.close()
        return jsonify(json_response)


def prepare_columns_and_values_when_adding_list(this_request, accountId):
    """
    Prepare columns and values for the database query.

    Args:
        this_request (dict): The dictionary containing the data for the new list entry.
        accountId (str): The account ID associated with the new list.

    Returns:
        tuple: A tuple containing lists of columns and column values.
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


def execute_database_query_when_adding_list(mydb, mycursor, accountId, account_list, columns, column_values):
    """
    Execute the database query to add a new list entry.

    Args:
        mydb: The MySQL database connection object.
        mycursor: The MySQL cursor object.
        accountId (str): The account ID associated with the list.
        account_list (str): The name of the database table to which the new list entry will be added.
        columns (list): A list of column names.
        column_values (list): A list of column values.

    Returns:
        str: The ID of the last inserted row.
    """

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    columns_for_query = " (" + ", ".join(columns) + ")"
    column_values_for_query = " ('" + "', '".join(column_values) + "')"

    mycursor.execute(f"INSERT INTO {account_list}{columns_for_query} VALUES{column_values_for_query}")
    mydb.commit()

    return str(mycursor.lastrowid)


def update_dynamically_linked_fields_when_adding_list(mydb, mycursor, accountId, account_list, this_request, last_row_id):
    """
    Update dynamically linked fields if necessary.

    Args:
        mydb: The MySQL database connection object.
        mycursor: The MySQL cursor object.
        accountId (str): The account ID associated with the dynamic linked fields.
        account_list (str): The name of the database table.
        this_request (dict): The dictionary containing the data for the new list entry.
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
        mycursor.execute(f"UPDATE {account_list} SET {final_key_to_update_dynamically} = {final_val_to_update_dynamically} WHERE id = '{last_row_id}'")
        mydb.commit()


def delete_dynamic_lists(request, accountId: str, account_list: str):
    """
    Delete selected entries from a dynamic list in the database.

    Args:
        request (Request): The HTTP request object containing the IDs of the entries to be deleted.
        accountId (str): The Account ID.
        account_list (str): The name of the database table from which entries will be deleted.

    Returns:
        jsonify: JSON response containing the remaining lists after deletion.
    """

    json_response = {"lists": []}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        # Extract data from the HTTP request
        entries_to_delete = werkzeug.utils.escape(request.form.get("entries_to_delete"))

        # Validate entries_to_delete to prevent SQL injection
        validate_entries_to_delete(entries_to_delete, accountId)

        # Delete selected entries from the database
        mycursor.execute(f"DELETE FROM {account_list} WHERE id IN ({entries_to_delete})")
        mydb.commit()

        # Retrieve the updated list of tables after deletion
        mycursor.execute(f"SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA=%s AND TABLE_NAME REGEXP %s", (Config.DB_NAME, account_list,))
        lists = mycursor.fetchall()

        json_response = {"lists": lists}

    except Exception as e:
        print("delete_dynamic_lists model")
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


def add_single_list(request):
    """
    Add a new list to the database.

    Args:
        request (Request): The HTTP request object containing data for the new list.

    Returns:
        jsonify: JSON response containing the details of the added list.
    """
    last_row = {}

    accountId = werkzeug.utils.escape(request.form.get("accountId"))

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        # Extract data from the HTTP request
        name = werkzeug.utils.escape(re.sub(r'[^a-zA-Z0-9_]', '', request.form.get("name")))
        reference = werkzeug.utils.escape(re.sub(r'[^a-zA-Z0-9_]', '', request.form.get("reference")))

        # Validate input data
        validate_input_data_to_add(name, reference, accountId)

        # Insert new list into the 'lists' table
        insert_query = "INSERT INTO lists (name, reference, accountId) VALUES (%s, %s, %s)"
        mycursor.execute(insert_query, (name, reference, accountId))
        mydb.commit()

        # Retrieve the details of the added list
        select_query = "SELECT * FROM lists WHERE accountId = %s AND reference = %s"
        mycursor.execute(select_query, (accountId, reference))
        last_row = mycursor.fetchone()

    except Exception as e:
        print("add_single_list model")
        print(e)
    finally:
        mydb.close()
        # Return JSON response containing the details of the added list
        return jsonify(last_row)


def validate_input_data_to_add(name, reference, accountId):
    """
    Validate input data to prevent SQL injection.

    Args:
        name (str): The name of the new list.
        reference (str): The reference code for the new list.
        accountId (str): The account ID associated with the new list.

    Raises:
        ValueError: If any input data is invalid.
    """

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    if not (name and reference and accountId.isdigit()):
        print("validate_input_data_to_add model")
        raise ValueError("Invalid input data for adding a new list.")


def update_single_list(request):
    """
    Update a list in the database.

    Args:
        request (Request): The HTTP request object containing data for the list update.

    Returns:
        jsonify: JSON response containing the details of the updated list.
    """
    json_response = {}

    accountId = werkzeug.utils.escape(request.form.get("accountId"))

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        reference = werkzeug.utils.escape(re.sub(r'[^a-zA-Z0-9_]', '', request.form.get("reference")))
        original_list_name = werkzeug.utils.escape(re.sub(r'[^a-zA-Z0-9_]', '', request.form.get("original_list_name")))
        new_list_name = werkzeug.utils.escape(re.sub(r'[^a-zA-Z0-9_]', '', request.form.get("new_list_name")))
        user_with_access = werkzeug.utils.escape(re.sub(r'[^a-zA-Z0-9_]', '', request.form.get("user_with_access")))

        # Validate input data
        validate_input_data_to_update(reference, accountId, original_list_name, new_list_name, user_with_access)

        # Update the list in the 'lists' table
        update_query = "UPDATE lists SET name=%s, reference=%s, user_with_access=%s WHERE name=%s AND accountId=%s"
        values = (new_list_name, reference, user_with_access, original_list_name, accountId)
        mycursor.execute(update_query, values)
        mydb.commit()

        json_response = {"name": new_list_name, "reference": reference}

    except Exception as e:
        print("update_single_list model")
        print(e)
    finally:
        if mydb:
            return jsonify(json_response)


def validate_input_data_to_update(reference, accountId, original_list_name, new_list_name, user_with_access):
    """
    Validate input data to prevent SQL injection.

    Args:
        reference (str): The reference code for the list.
        accountId (str): The account ID associated with the list.
        original_list_name (str): The original name of the list.
        new_list_name (str): The new name for the list.
        user_with_access (str): User with access to the list.

    Raises:
        ValueError: If any input data is invalid.
    """

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    if not all((reference, accountId.isdigit(), original_list_name, new_list_name, user_with_access)):
        print("validate_input_data_to_update model")
        raise ValueError("Invalid input data for updating a list.")


def delete_multiple_lists(request):
    """
    Delete multiple lists from the database.

    Args:
        request (Request): The HTTP request object containing data for the lists deletion.

    Returns:
        jsonify: JSON response containing information about the deleted lists.
    """
    json_response = {}

    accountId = werkzeug.utils.escape(request.form.get("accountId"))

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    lists_to_delete = werkzeug.utils.escape(request.form.get("lists_to_delete"))

    if not lists_to_delete:
        json_response = {"lists_to_delete": "None provided", "action": "none"}
        return jsonify(json_response)

    # Convert the string to a list
    lists_to_delete = [list_name.strip() for list_name in lists_to_delete.split(",")]

    mydb, mycursor = db_connection()

    try:
        # Delete rows from the 'lists' table
        delete_query = "DELETE FROM lists WHERE name IN (%s)"  # Removed the accountId condition temporarily
        placeholders = ",".join(["%s"] * len(lists_to_delete))
        delete_query = f"{delete_query} AND accountId=%s"  # Add accountId condition back
        values = lists_to_delete + [accountId]  # Add accountId to values
        mycursor.execute(delete_query, values)
        mydb.commit()

        # Drop corresponding tables
        for list_name in lists_to_delete:
            # Validate input data
            validate_input_data_to_delete(list_name, accountId)

            table_name = f"account_{accountId}_list_{list_name}"
            mycursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            mydb.commit()

        json_response = {"lists_to_delete": lists_to_delete, "action": "deleted"}

    except Exception as e:
        print("delete_multiple_lists model")
        print(e)
    finally:
        mydb.close()
        return jsonify(json_response)


def delete_single_list(request):
    """
    Delete a list from the database.

    Args:
        request (Request): The HTTP request object containing data for the list deletion.

    Returns:
        jsonify: JSON response containing information about the deleted list.

    Raises:
        RuntimeError: An exception raised in case of any error during database operations.
    """
    json_response = {}

    accountId = werkzeug.utils.escape(request.form.get("accountId"))

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    name = werkzeug.utils.escape(request.form.get("name"))

    # Validate input data
    validate_input_data_to_delete(name, accountId)

    mydb, mycursor = db_connection()

    try:
        # Delete row from the 'lists' table
        delete_query = "DELETE FROM lists WHERE name=%s AND accountId=%s"
        values = (name, accountId)
        mycursor.execute(delete_query, values)
        mydb.commit()

        json_response = {"name": name, "action": "deleted"}

    except Exception as e:
        print("delete_single_list model")
        print(e)
    finally:
        mydb.close()
        return jsonify(json_response)


def validate_input_data_to_delete(list_to_delete, accountId):
    """
    Validate input data to prevent SQL injection.

    Args:
        list_to_delete (str): Comma-separated list of lists to delete.
        accountId (str): The account ID associated with the lists.

    Raises:
        ValueError: If any input data is invalid.
    """

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    if not all((list_to_delete, accountId.isdigit())):
        print("validate_input_data_to_delete model")
        raise ValueError("Invalid input data for deleting list.")


def list_belongs_to_account(list_id):
    """
    Check if the specified list ID belongs to the specified account ID.

    Args:
        list_id (int): The ID of the list to check.

    Returns:
        bool: True if the site belongs to the account, False otherwise.
    """

    try:
        accountId = session["accountId"]
        mydb, mycursor = db_connection()

        # Check if the site ID belongs to the specified account
        mycursor.execute("SELECT COUNT(*) FROM lists WHERE id = %s AND accountId = %s", (list_id, accountId))
        result = mycursor.fetchone()

        # If there is at least one matching record, the site belongs to the account
        return result[0] > 0

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        print(f"An error occurred: {str(e)}")
        return False
