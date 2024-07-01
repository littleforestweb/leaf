# models.py

import csv
import html
import json
import traceback
from datetime import datetime
from typing import Tuple

import chardet
import pandas as pd
import werkzeug.utils
from flask import current_app
from markupsafe import Markup

from leaf.sites.models import get_user_access_folder
from leaf.template_editor.models import *


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


def build_folder_access_where_clause(folder_access_field, user_access_folder):
    where_clauses = []
    for path in user_access_folder:
        my_path_value = path[1:]
        if my_path_value.endswith('/'):
            my_path_value = my_path_value.rstrip('/')
        clause = "SUBSTRING_INDEX(value, '/', 1) LIKE %s"
        where_clauses.append((clause, my_path_value))
    return where_clauses


def get_list_data(request, accountId: str, reference: str):
    jsonR = {'data': [], 'recordsTotal': 0, 'recordsFiltered': 0}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        limit = int(request.args.get("iDisplayLength"))
        skip = int(request.args.get("iDisplayStart"))
        direction = request.args.get("sSortDir_0").upper()
        sortingColumn = request.args.get("iSortCol_0")

        has_folder_access_defined = False
        folder_access_field = False
        list_settings = get_list_columns_with_properties(accountId, reference)
        list_settings_str = list_settings.get_data(as_text=True)
        list_settings = json.loads(list_settings_str)["columns"]
        for list_setting in list_settings:
            if list_setting[3] == "-_leaf_access_folders_-":
                has_folder_access_defined = True
                folder_access_field = list_setting[2]

        user_access_folder = get_user_access_folder()

        if isinstance(int(accountId), int):
            tableName = f"account_{accountId}_list_{reference}"
            showColumnsQuery = f"SHOW COLUMNS FROM {tableName}"
            mycursor.execute(showColumnsQuery)
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

            userUsernameEmail = 'CONCAT(user.id, ", ", user.username, ", ", user.email)'
            columnsFinal = [f"{tableName}.{row[0]}" if row[0] != 'modified_by' else f"{userUsernameEmail}" for row in listColumns]

            # Constructing folder access where clause
            folder_where_clauses = build_folder_access_where_clause(folder_access_field, user_access_folder)
            folder_where_clause = " OR ".join([clause for clause, _ in folder_where_clauses])
            folder_where_params = [f"{value}" for _, value in folder_where_clauses]

            folder_where_clause_start = f"""
            {tableName}.id IN (
                SELECT DISTINCT id
                FROM (
                    SELECT id,
                           TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX({folder_access_field}, ',', numbers.n), ',', -1)) AS value
                    FROM {tableName}
                    JOIN (
                        SELECT 1 n UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL
                        SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL
                        SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL SELECT 10
                    ) numbers
                    WHERE numbers.n <= 1 + LENGTH({folder_access_field}) - LENGTH(REPLACE({folder_access_field}, ',', ''))
                ) split_values
                """
            folder_where_clause = f"{folder_where_clause_start} WHERE {folder_where_clause})"

            # Combine where clauses if both exist
            query_params = []
            if field_list and has_folder_access_defined and session["is_admin"] != 1:
                where_clause = f"({' AND '.join(field_list)}) AND ({folder_where_clause})"
                query_params = [f"%{searchColumnsField['value']}%" for searchColumnsField in searchColumnsFields] + folder_where_params
            elif field_list:
                where_clause = " AND ".join(field_list)
                query_params = [f"%{searchColumnsField['value']}%" for searchColumnsField in searchColumnsFields]
            elif has_folder_access_defined and session["is_admin"] != 1:
                where_clause = folder_where_clause
                query_params = folder_where_params
            else:
                where_clause = ""

            if where_clause != "":
                where_clause = f"WHERE {where_clause}"

            if field_list:
                query = f"""
                SELECT {', '.join(columnsFinal)} 
                FROM {tableName} 
                INNER JOIN user ON {tableName}.modified_by = user.id 
                {where_clause} 
                ORDER BY {listColumns[int(sortingColumn) - 1][0]} {direction} 
                LIMIT %s, %s
                """
                mycursor.execute(query, query_params + [skip, limit])
            else:
                order_by = listColumns[int(sortingColumn) - 1][0]
                query = f"""
                SELECT {', '.join(columnsFinal)} 
                FROM {tableName} 
                INNER JOIN user ON {tableName}.modified_by = user.id 
                {where_clause} 
                ORDER BY {order_by} {direction} 
                LIMIT %s, %s
                """
                mycursor.execute(query, query_params + [skip, limit])

            lists = mycursor.fetchall()
            mycursor.execute(f"SELECT COUNT(*) FROM {tableName} {where_clause}", query_params)
            listCount = mycursor.fetchone()[0]

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
            create_table_query = f"CREATE TABLE IF NOT EXISTS {tableName} (id INT(11) AUTO_INCREMENT PRIMARY KEY UNIQUE, name VARCHAR(255), modified_by INT(11) DEFAULT NULL)"
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
        if isinstance(int(accountId), int):
            tableName = f"account_{accountId}_list_{reference}"

            # Create table if not exists
            create_table_query = f"CREATE TABLE IF NOT EXISTS {tableName} (id INT(11) AUTO_INCREMENT PRIMARY KEY UNIQUE, name VARCHAR(255))"
            print(create_table_query)
            mycursor.execute(create_table_query, )
            mydb.commit()

            # Retrieve column information
            show_columns_query = f"SHOW COLUMNS FROM {tableName}"
            mycursor.execute(show_columns_query, )
            columns_info = mycursor.fetchall()

            # Convert bytes to string for column names
            columns_info = [(item[0], item[1], item[2], item[3], item[4], item[5]) for item in columns_info]

            jsonR['columns'] = columns_info
        else:
            print("Invalid accountId")

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


def get_list_configuration(accountId: str, reference: str, passed_session=None):
    """
    Get configuration information for a specific list from the database.

    Args:
        accountId (str): The account ID associated with the list.
        reference (str): The reference code for the specific list.

    Returns:
        dict: A JSON response containing configuration information for the specified list.
    """
    jsonR = {'columns': []}

    if passed_session is None:
        # Use the actual session variable
        actual_account_id = session["accountId"]
    else:
        # Use the passed session value
        actual_account_id = passed_session.get("accountId")

    if not int(accountId) == int(actual_account_id):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    if isinstance(int(accountId), int):

        field_list_for_config = ['id INT(11) AUTO_INCREMENT PRIMARY KEY UNIQUE',
                                 'main_table VARCHAR(255) DEFAULT NULL',
                                 'mandatory_fields VARCHAR(255) DEFAULT NULL',
                                 'save_by_field VARCHAR(11) DEFAULT 0',
                                 'field_to_save_by VARCHAR(255) DEFAULT NULL',
                                 'created_by INT(11) DEFAULT NULL',
                                 'modified_by INT(11) DEFAULT NULL',
                                 'created DATETIME NULL DEFAULT CURRENT_TIMESTAMP',
                                 'modified DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP']
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

    if passed_session is None:
        return jsonify(jsonR)
    else:
        return jsonR


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

            mfields = werkzeug.utils.escape(thisRequest.get("s-mandatory-fields"))
            save_by_field = werkzeug.utils.escape(thisRequest.get("s-save-by-field"))
            field_to_save_by = werkzeug.utils.escape(thisRequest.get("s-field-to-save-by"))
            field_to_save_by_includes = werkzeug.utils.escape(thisRequest.get("s-field-to-save-by-includes"))
            modified_by = session["id"]

            if isinstance(mfields, list):
                mfields = ';'.join(mfields)

            if isinstance(field_to_save_by, list):
                field_to_save_by = ';'.join(field_to_save_by)

            col_to_return = [mfields, save_by_field, field_to_save_by, modified_by]

            add_column_if_not_exists(mycursor, tableName, "field_to_save_by_includes", "TEXT", "field_to_save_by")

            # Insert new configuration for the specified list
            insert_config_query = f"INSERT INTO {tableName} (main_table, mandatory_fields, save_by_field, field_to_save_by, field_to_save_by_includes, created_by, modified_by) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            mycursor.execute(insert_config_query, (reference, mfields, save_by_field, field_to_save_by, field_to_save_by_includes, modified_by, modified_by))
            mydb.commit()
        else:
            print("Invalid accountId")

    except Exception as e:
        print("set_list_configuration model")
        print(e)
    finally:
        mydb.close()
        return jsonify(col_to_return)


def get_all_templates(request, accountId: str):
    """
    Get templates information for a specific account from the database.

    Args:
        accountId (str): The account ID associated with the list.

    Returns:
        dict: A JSON response containing templates information for the specified account.
    """
    jsonR = {'data': [], 'recordsTotal': 0, 'recordsFiltered': 0}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    limit = False
    skip = False
    direction = "-1"
    sortingColumn = False
    if request.args.get("iDisplayLength"):
        limit = int(request.args.get("iDisplayLength"))
    if request.args.get("iDisplayStart"):
        skip = int(request.args.get("iDisplayStart"))
    if request.args.get("sSortDir_0"):
        direction = request.args.get("sSortDir_0").upper()
    if request.args.get("iSortCol_0"):
        sortingColumn = request.args.get("iSortCol_0")

    if isinstance(int(accountId), int):

        field_list_for_config = ['id INT(11) AUTO_INCREMENT PRIMARY KEY UNIQUE',
                                 'in_lists VARCHAR(255) DEFAULT NULL',
                                 'template VARCHAR(255) DEFAULT NULL',
                                 'template_location VARCHAR(255) DEFAULT NULL',
                                 'feed_location VARCHAR(255) DEFAULT NULL',
                                 'modified_by INT(11) DEFAULT NULL',
                                 'created DATETIME NULL DEFAULT CURRENT_TIMESTAMP',
                                 'modified DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP']
        field_query_for_config = " (" + ", ".join(field_list_for_config) + ")"

        tableName = f"account_{accountId}_list_template"

        # Create table if not exists
        create_table_query = f"CREATE TABLE IF NOT EXISTS {tableName} {field_query_for_config}"
        mycursor.execute(create_table_query, )
        mydb.commit()

        showColumnsQuery = f"SHOW COLUMNS FROM {tableName}"
        mycursor.execute(showColumnsQuery, )
        listColumns = mycursor.fetchall()

        if sortingColumn:
            searchColumnsFields = []
            field_list = []

            search_value_1 = request.args.get(f"sSearch_1")
            search_value_2 = request.args.get(f"sSearch_2")
            search_value_3 = request.args.get(f"sSearch_3")
            search_value_4 = request.args.get(f"sSearch_4")
            search_value_5 = request.args.get(f"sSearch_5")
            if search_value_1:
                searchColumnsFields.append({"field": "template", "value": search_value_1.replace("((((", "").replace("))))", "")})
            if search_value_2:
                searchColumnsFields.append({"field": "template_location", "value": search_value_2.replace("((((", "").replace("))))", "")})
            if search_value_3:
                searchColumnsFields.append({"field": "feed_location", "value": search_value_3.replace("((((", "").replace("))))", "")})
            if search_value_4:
                searchColumnsFields.append({"field": "in_lists", "value": search_value_4.replace("((((", "").replace("))))", "")})
            if search_value_5:
                # searchColumnsFields.append({"field": "user.id", "value": search_value_5.replace("((((", "").replace("))))", "")})
                # searchColumnsFields.append({"field": "user.username", "value": search_value_5.replace("((((", "").replace("))))", "")})
                searchColumnsFields.append({"field": "user.email", "value": search_value_5.replace("((((", "").replace("))))", "")})

            for searchColumnsField in searchColumnsFields:
                searchColumnsFieldValue = searchColumnsField['value'].replace('"', "'")
                field_list.append(f"{searchColumnsField['field']} LIKE %s")

            userUsernameEmail = 'CONCAT(user.id, ", ", user.username, ", ", user.email)'
            columnsFinal = [f"{tableName}.{row[0]}" if row[0] != 'modified_by' else f"{userUsernameEmail}" for row in listColumns]

            where_clause = " AND ".join(field_list)
            if field_list:
                query_params = list(f"%{searchColumnsField['value']}%" for searchColumnsField in searchColumnsFields)
                get_templates_query = f"SELECT {', '.join(columnsFinal)} FROM {tableName} INNER JOIN user ON {tableName}.modified_by = user.id WHERE {where_clause} ORDER BY {listColumns[int(sortingColumn) - 1][0]} {direction} LIMIT %s, %s"
                mycursor.execute(get_templates_query, query_params + [skip, limit])
            else:
                order_by = listColumns[int(sortingColumn)][0]
                get_templates_query = f"SELECT {', '.join(columnsFinal)} FROM {tableName} INNER JOIN user ON {tableName}.modified_by = user.id ORDER BY {order_by} {direction} LIMIT %s, %s"
                mycursor.execute(get_templates_query, (skip, limit))

            config_info = mycursor.fetchall()

        else:
            # Retrieve templates information
            get_templates_query = f"SELECT * FROM {tableName} ORDER BY template {direction}"
            mycursor.execute(get_templates_query)
            config_info = mycursor.fetchall()

        mycursor.execute(f"SELECT COUNT(*) FROM {tableName}")
        listCount = mycursor.fetchone()[0]

        jsonR['data'] = config_info
        jsonR['recordsTotal'] = listCount
        jsonR['recordsFiltered'] = len(config_info)
    else:
        print("Invalid accountId")

    return jsonify(jsonR)


def get_list_template(accountId: str, reference: str):
    """
    Get template information for a specific list from the database.

    Args:
        accountId (str): The account ID associated with the list.
        reference (str): The reference code for the specific list.

    Returns:
        dict: A JSON response containing template information for the specified list.
    """
    jsonR = {'columns': []}

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    if isinstance(int(accountId), int):

        field_list_for_config = ['id INT(11) AUTO_INCREMENT PRIMARY KEY UNIQUE',
                                 'in_lists VARCHAR(255) DEFAULT NULL',
                                 'template VARCHAR(255) DEFAULT NULL',
                                 'template_location VARCHAR(255) DEFAULT NULL',
                                 'feed_location VARCHAR(255) DEFAULT NULL',
                                 'modified_by INT(11) DEFAULT NULL',
                                 'created DATETIME NULL DEFAULT CURRENT_TIMESTAMP',
                                 'modified DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP']
        field_query_for_config = " (" + ", ".join(field_list_for_config) + ")"

        tableName = f"account_{accountId}_list_template"

        # Create table if not exists
        create_table_query = f"CREATE TABLE IF NOT EXISTS {tableName} {field_query_for_config}"
        mycursor.execute(create_table_query, )
        mydb.commit()

        # Retrieve templates information
        get_templates_query = f"SELECT * FROM {tableName} WHERE in_lists = %s"
        mycursor.execute(get_templates_query, (reference,))
        template_info = mycursor.fetchall()

        jsonR['columns'] = template_info
    else:
        print("Invalid accountId")

    return jsonify(jsonR)


def set_list_template(request, accountId: str, reference: str):
    """
    Set template for a specific list in the database.

    Args:
        request (Request): The HTTP request object.
        accountId (str): The account ID associated with the list.
        reference (str): The reference code for the specific list.

    Returns:
        list: A list containing the values that were inserted into the database for template.
    """
    col_to_return = []

    thisRequest = request.get_json()

    template = str(thisRequest.get("s-templates"))
    template = template.lower()
    template = ''.join(c if c.isalnum() else '_' for c in template)
    template = werkzeug.utils.escape(template)

    template_location = werkzeug.utils.escape(str(thisRequest.get("s-template_location")))
    feed_location = werkzeug.utils.escape(str(thisRequest.get("s-feed_location")))

    if not template.endswith("_html"):
        template += ".html"
    template = template.replace("_html", ".html")

    if reference == '____no_list_selected____':
        reference = ""

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        tableName = f"account_{accountId}_list_template"

        if isinstance(int(accountId), int):
            # Delete existing template

            templates_format = werkzeug.utils.escape(str(thisRequest.get("s-templates_format")))

            if templates_format and templates_format == "select":
                get_templates_query = f"SELECT * FROM {tableName} WHERE id = %s"
                mycursor.execute(get_templates_query, (template,))
                template_info = mycursor.fetchall()
                template_file = template_info[0][2]
                template = template_file

                update_config_query = f"UPDATE {tableName} SET in_lists = '', template_location = %s, feed_location = %s, modified = CURRENT_TIMESTAMP WHERE in_lists = %s"
                mycursor.execute(update_config_query, (template_location, feed_location, reference))
                mydb.commit()

            if templates_format and templates_format == "input":
                delete_config_query = f"DELETE FROM {tableName} WHERE template = %s"
                mycursor.execute(delete_config_query, (template,))
                mydb.commit()

            modified_by = int(session["id"])

            col_to_return = [template, template_location, feed_location, modified_by]

            if templates_format and templates_format == "select":
                # Update template
                update_config_query = f"UPDATE {tableName} SET in_lists = %s, template_location = %s, feed_location = %s, modified_by = %s, modified = CURRENT_TIMESTAMP WHERE template = %s"
                mycursor.execute(update_config_query, (reference, template_location, feed_location, modified_by, template))
                mydb.commit()
            else:
                # Insert new template
                insert_config_query = f"INSERT INTO {tableName} (in_lists, template, template_location, feed_location, modified_by) VALUES (%s, %s, %s, %s, %s)"
                mycursor.execute(insert_config_query, (reference, template, template_location, feed_location, modified_by))
                mydb.commit()

            if templates_format and templates_format == "input":
                # Save new template in the correct folder
                file_to_save = os.path.join(Config.TEMPLATES_FOLDER, accountId, template.strip("/"))
                folder_to_save_item = os.path.dirname(file_to_save)
                os.makedirs(folder_to_save_item, exist_ok=True)
                with open(file_to_save, 'w') as out_file:
                    out_file.write('<html><body><h1>Hi, this is a new template! Start editing here</h1></body></html>')
        else:
            print("Invalid accountId")

    except Exception as e:
        print("set_list_template model")
        print(e)
    finally:
        mydb.close()
        return jsonify(col_to_return)


def delete_templates(request, accountId: str):
    """
    Delete selected entries from a templates list in the database.

    Args:
        request (Request): The HTTP request object containing the IDs of the entries to be deleted.
        accountId (str): The Account ID.

    Returns:
        jsonify: JSON response containing the remaining templates after deletion.
    """

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    col_to_return = []
    template_to_delete = werkzeug.utils.escape(request.form.get("template_to_delete"))

    # Validate entries_to_delete to prevent SQL injection
    validate_entries_to_delete(template_to_delete, accountId)

    mydb, mycursor = db_connection()

    try:
        tableName = f"account_{accountId}_list_template"

        if isinstance(int(accountId), int):

            # Retrieve template information
            get_templates_query = f"SELECT * FROM {tableName} WHERE id = %s"
            mycursor.execute(get_templates_query, (template_to_delete,))
            template_info = mycursor.fetchall()
            template_file = template_info[0][2]

            # Delete existing template
            file_to_delete = os.path.join(Config.TEMPLATES_FOLDER, accountId, template_file)
            if os.path.exists(file_to_delete):
                os.remove(file_to_delete)
                print(f"File '{file_to_delete}' deleted successfully.")
            else:
                print(f"File '{file_to_delete}' does not exist.")

            mycursor.execute(f"DELETE FROM {tableName} WHERE id IN (%s)", (template_to_delete,))
            mydb.commit()

        else:
            print("Invalid accountId")

    except Exception as e:
        print("delete_templates model")
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
            col_names_to_generate_fields = [field.strip().lower() for field in col_names if field.strip().lower() != 'id']

            field_list = ['id INT(11) AUTO_INCREMENT PRIMARY KEY UNIQUE']

            # Loop through the column names to generate their fields
            for field in col_names_to_generate_fields:
                field_list.append(f'{field} LONGTEXT DEFAULT NULL')

            # We will make this an dynamic input so the user can select if there's a field with the created date value
            modified_by_names = ['modifiedby', 'modified-by', 'modified_by']
            # We will make this an dynamic input so the user can select if there's a field with the created date value
            created_names = ['created', 'created-date', 'created_date', 'createddate']
            # We will make this an dynamic input so the user can select if there's a field with the modified date value
            modified_names = ['modified', 'modified-date', 'modified_date', 'modifieddate']
            # We will make this an dynamic input so the user can select if there's a field with the publication date value
            publication_names = ['pubdate', 'pub-date', 'pub_date', 'publication_date', 'publication-date', 'publicationdate']

            foundModified_by = False
            foundCreated = False
            foundModified = False
            foundPublication = False

            for modified_by_name in modified_by_names:
                if modified_by_name.strip().lower() in col_names_to_generate_fields:
                    foundModified_by = True
                    print(f"{modified_by_name} variable exists in the list.")
                    break

            for created_name in created_names:
                if created_name.strip().lower() in col_names_to_generate_fields:
                    foundCreated = True
                    print(f"{created_name} variable exists in the list.")
                    break

            for modified_name in modified_names:
                if modified_name.strip().lower() in col_names_to_generate_fields:
                    foundModified = True
                    print(f"{modified_name} variable exists in the list.")
                    break

            for publication_name in publication_names:
                if publication_name.strip().lower() in col_names_to_generate_fields:
                    foundPublication = True
                    print(f"{publication_name} variable exists in the list.")
                    break

            # Additional fields for tracking modifications and timestamps
            if not foundModified_by:
                field_list.append(f'modified_by INT(11) DEFAULT NULL')  # Track who modified the record
                col_names.append(f'modified_by')
            if not foundCreated:
                field_list.append(f'created DATETIME NULL DEFAULT CURRENT_TIMESTAMP')  # Track creation timestamp
                col_names.append(f'created')
            if not foundModified:
                field_list.append(f'modified DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')  # Track modification timestamp
                col_names.append(f'modified')
            if not foundPublication:
                field_list.append(f'publication_date DATETIME NULL DEFAULT CURRENT_TIMESTAMP')  # Track publication date timestamp
                col_names.append(f'publication_date')

            field_query = " (" + ", ".join(field_list) + ")"

            # Create table if not exists
            create_table_query = f"CREATE TABLE IF NOT EXISTS {tableName}{field_query}"
            mycursor.execute(create_table_query, )
            mydb.commit()

            # Use Pandas to parse the CSV file
            csv_data = pd.read_csv(filePath, sep=",", encoding="utf-8", encoding_errors='ignore', engine="python", header=None)  # names=col_names,

            insert_query = f"INSERT INTO {tableName} ({', '.join(col_names)}) VALUES "

            dateTimeNow = datetime.now()

            # Loop through the rows
            for i, row in csv_data.iterrows():
                if i != 0:
                    values = map((lambda x: f'"' + html.escape(str((x if isinstance(x, float) else x.encode('utf-8'))).replace("\\", "__BACKSLASH__TO_REPLACE__")[2:-1]) + '"'), row)
                    joint_value = ', '.join(values)

                    if not foundModified_by:
                        joint_value = joint_value + ', ' + str(session["id"])

                    if not foundCreated:
                        joint_value = joint_value + ', ' + "'" + dateTimeNow.strftime('%Y-%m-%d %H:%M:%S') + "'"

                    if not foundModified:
                        joint_value = joint_value + ', ' + "'" + dateTimeNow.strftime('%Y-%m-%d %H:%M:%S') + "'"

                    if not foundPublication:
                        joint_value = joint_value + ', ' + "'" + dateTimeNow.strftime('%Y-%m-%d %H:%M:%S') + "'"

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
                    if val != "null" and val != '-_leaf_users_-' and val != '-_leaf_access_folders_-':
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
                "original_images_webpath": Config.ORIGINAL_IMAGES_WEBPATH,
                "preview_server": Config.PREVIEW_SERVER
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


def generate_all_json_files_by_fields(request, account_list: str, accountId: str, reference: str):
    """
    Generate dynamic list data to JSON files by field.

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

        this_request = request.get_json()

        sanitized_reference = ''.join(e for e in reference if e.isalnum())

        save_by_field = werkzeug.utils.escape(this_request.get("save_by_field"))
        field_to_save_by = werkzeug.utils.escape(this_request.get("field_to_save_by"))

        fields_to_save = f"""
        SELECT DISTINCT TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(paths.value, ',', numbers.n), ',', -1)) AS unique_value
        FROM (
            SELECT {field_to_save_by} AS value FROM leaf.{account_list}
        ) paths
        JOIN (
            SELECT 1 n UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL
            SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL
            SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL SELECT 10
        ) numbers ON CHAR_LENGTH(paths.value) - CHAR_LENGTH(REPLACE(paths.value, ',', '')) >= numbers.n - 1
        ORDER BY unique_value;
        """
        mycursor.execute(fields_to_save)
        fields_to_save = mycursor.fetchall()
        unique_fields_to_save = [row[0] for row in fields_to_save]

        field_to_save_by_includes = werkzeug.utils.escape(this_request.get("field_to_save_by_includes"))
        if field_to_save_by != "False":
            for this_field_to_save in unique_fields_to_save:
                # Construct the SQL query with multiple FIND_IN_SET conditions
                by_field_query = f"SELECT {field_to_save_by_includes} FROM {account_list} WHERE FIND_IN_SET(%s, `{field_to_save_by}`)"
                mycursor.execute(by_field_query, (this_field_to_save,))
                row_headers = [x[0] for x in mycursor.description]
                full_list_by_field = mycursor.fetchall()

                # Convert data to a JSON format
                json_data_by_field = [dict(zip(row_headers, result)) for result in full_list_by_field]
                json_data_to_write_by_field = json.dumps(json_data_by_field, default=custom_serializer).replace('__BACKSLASH__TO_REPLACE__', '\\')

                # Write JSON data to a file with the field-specific reference identifier (sanitize reference)
                sanitized_save_by_field = ''.join(e for e in (this_field_to_save.replace("/", "leaffslash").replace("-", "leafhiffen").strip().lower()) if e.isalnum())
                sanitized_save_by_field = sanitized_save_by_field.replace("leaffslash", "__fslash__").replace("leafhiffen", "-")

                os.makedirs(os.path.join(Config.WEBSERVER_FOLDER, Config.DYNAMIC_PATH, 'json_by_field'), exist_ok=True)
                with open(os.path.join(Config.WEBSERVER_FOLDER, Config.DYNAMIC_PATH, 'json_by_field', sanitized_reference + "_" + sanitized_save_by_field + '_List.json'), 'w') as out_file_by_field:
                    out_file_by_field.write(json_data_to_write_by_field)

    except Exception as e:
        print("generate_all_json_files_by_fields model")
        print(e)
    finally:
        mydb.close()
        return jsonify({"full_list": full_list})


def ensure_canonical_link(html_str, canonical_url):
    soup = BeautifulSoup(html_str, 'html.parser')

    # Check if there's a rel="canonical" link tag
    canonical_tag = soup.find('link', rel='canonical')

    if canonical_tag:
        # Update the href attribute to the correct canonical URL
        canonical_tag['href'] = canonical_url
    else:
        # Create a new link tag with rel="canonical"
        new_tag = soup.new_tag('link', rel='canonical', href=canonical_url)

        # Insert the new tag into the head of the document
        if soup.head:
            soup.head.append(new_tag)
        else:
            # If there's no head tag, create one and insert the new link tag
            head_tag = soup.new_tag('head')
            head_tag.append(new_tag)
            soup.insert(0, head_tag)

    return str(soup)


def publish_dynamic_lists(request, account_list: str, accountId: str, reference: str, env: str):
    """
    Publish dynamic list data to JSON files and optionally by field.

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
        full_list_by_field = []

        this_request = request.get_json()
        file_url_paths = this_request.get("file_url_path")
        list_template_id = werkzeug.utils.escape(this_request.get("list_template_id"))
        list_item_id = werkzeug.utils.escape(this_request.get("list_item_id"))
        current_app.logger.debug("list_item_id:")
        current_app.logger.debug(list_item_id)

        mycursor.execute(f"SELECT * FROM {account_list} WHERE id = %s", (list_item_id,))
        selected_item_id = mycursor.fetchone()

        # Combine column names with fetched row values
        selected_item_data = dict(zip(row_headers, selected_item_id))

        list_template_html = templates_get_template_html(accountId, list_template_id)

        # Replace html_placeholders with actual values from the selected_item_data
        for key, value in selected_item_data.items():
            html_placeholder = '{{' + key + '}}'
            if html_placeholder in list_template_html:
                if value is not None:
                    list_template_html = list_template_html.replace(html_placeholder, unescape_html(value))

        # Remove any HTML elements that contain html_placeholders that do not exist in the selected_item_data
        html_placeholders = re.findall(r'{{(.*?)}}', list_template_html)
        for placeholder in html_placeholders:
            element_with_placeholder = re.sub(r'{{\w+}}', '', placeholder)  # Remove the placeholder to check for existence
            if not any(placeholder in selected_item_data for placeholder in re.findall(r'{{(\w+)}}', element_with_placeholder)):
                list_template_html = remove_elements_with_content_or_src(list_template_html, "{{" + placeholder + "}}")
                # Removed remaining unused tags
                list_template_html = list_template_html.replace("{{" + placeholder + "}}", '')

        # Save new page in the correct folder based on template
        for file_url_path in file_url_paths:
            file_url_path = werkzeug.utils.escape(file_url_path)

            # Ensure we save with the correct canonical link
            canonical_url = os.path.join(Config.PREVIEW_SERVER, file_url_path.strip("/"))
            list_template_html_updated = ensure_canonical_link(list_template_html, canonical_url)

            file_to_save = os.path.join(Config.WEBSERVER_FOLDER, file_url_path.strip("/"))
            folder_to_save_item = os.path.dirname(file_to_save)
            os.makedirs(folder_to_save_item, exist_ok=True)
            with open(file_to_save, 'w') as out_file:
                out_file.write(list_template_html_updated)

        # Convert data to a JSON format
        # json_data = [dict(zip(row_headers, result)) for result in full_list]
        # json_data_to_write = json.dumps(json_data, default=custom_serializer).replace('__BACKSLASH__TO_REPLACE__', '\\')

        # # Write JSON data to a file with the specified reference identifier (sanitize reference)
        sanitized_reference = ''.join(e for e in reference if e.isalnum())
        # os.makedirs(os.path.join(Config.WEBSERVER_FOLDER, Config.DYNAMIC_PATH), exist_ok=True)
        # with open(os.path.join(Config.WEBSERVER_FOLDER, Config.DYNAMIC_PATH, sanitized_reference + 'List.json'), 'w') as out_file:
        #     out_file.write(json_data_to_write)

        # Additional logic to save data by field (sanitize user input)
        save_by_field = werkzeug.utils.escape(this_request.get("save_by_field"))
        field_to_save_by = werkzeug.utils.escape(this_request.get("field_to_save_by"))
        field_to_save_by_includes = werkzeug.utils.escape(this_request.get("field_to_save_by_includes"))

        if field_to_save_by != "False" and save_by_field != "false":
            # Query to retrieve data filtered by field (using parameterized query)
            # Convert to string if it is Markup
            if isinstance(save_by_field, Markup):
                save_by_field = str(save_by_field)
            # Split the save_by_field into individual paths
            save_by_field = save_by_field.split(",")

            for this_field_to_save in save_by_field:
                this_field_to_save = this_field_to_save.split(",")
                # Construct the SQL query with multiple FIND_IN_SET conditions
                by_field_conditions = " OR ".join([f"FIND_IN_SET(%s, `{field_to_save_by}`)" for _ in this_field_to_save])
                by_field_query = f"SELECT {field_to_save_by_includes} FROM {account_list} WHERE {by_field_conditions}"
                mycursor.execute(by_field_query, tuple(this_field_to_save))
                row_headers = [x[0] for x in mycursor.description]
                full_list_by_field = mycursor.fetchall()

                # Convert data to a JSON format
                json_data_by_field = [dict(zip(row_headers, result)) for result in full_list_by_field]
                json_data_to_write_by_field = json.dumps(json_data_by_field, default=custom_serializer).replace('__BACKSLASH__TO_REPLACE__', '\\')

                # Write JSON data to a file with the field-specific reference identifier (sanitize reference)
                sanitized_save_by_field = ''.join(e for e in (this_field_to_save[0].replace("/", "leaffslash").replace("-", "leafhiffen").strip().lower()) if e.isalnum())
                sanitized_save_by_field = sanitized_save_by_field.replace("leaffslash", "__fslash__").replace("leafhiffen", "-")

                os.makedirs(os.path.join(Config.WEBSERVER_FOLDER, Config.DYNAMIC_PATH, 'json_by_field'), exist_ok=True)
                with open(os.path.join(Config.WEBSERVER_FOLDER, Config.DYNAMIC_PATH, 'json_by_field', sanitized_reference + "_" + sanitized_save_by_field + '_List.json'), 'w') as out_file_by_field:
                    out_file_by_field.write(json_data_to_write_by_field)

    except Exception as e:
        current_app.logger.debug("publish_dynamic_lists model")
        current_app.logger.debug(e)
        current_app.logger.debug(traceback.format_exc())
    finally:
        mydb.close()
        return jsonify({"full_list": full_list_by_field})


def add_column_if_not_exists(cursor, table_name, column_name, column_definition, after_column):
    # Check if the column exists
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table_name}' AND COLUMN_NAME = '{column_name}'
    """)
    if cursor.fetchone()[0] == 0:
        # Column does not exist, so add it
        if after_column:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition} AFTER {after_column}")
        else:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")


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

            leaf_selected_rss = this_request.get('leaf_selected_rss', [])
            rss_string = ','.join(leaf_selected_rss)

            # Add the column if it does not exist
            add_column_if_not_exists(mycursor, account_list, "leaf_selected_rss", "TEXT", False)

            mycursor.execute(f"UPDATE {account_list} SET leaf_selected_rss = %s, modified = CURRENT_TIMESTAMP WHERE id = %s", (rss_string, item_id))
            mydb.commit()

            for key, val in this_request.items():
                if key.startswith("e-"):
                    final_key = key.replace("e-", "")
                    columns_to_return.append(final_key)

                    if isinstance(val, list):
                        val = ';'.join(val)

                    # Update the database with the new value (use parameterized query to prevent SQL injection)
                    if final_key != 'id' and final_key != 'leaf_selected_rss':
                        final_val = val.replace('"', "'")
                        mycursor.execute(f"UPDATE {account_list} SET {final_key} = %s, modified = CURRENT_TIMESTAMP WHERE id = %s", (final_val, item_id))
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

    columns.append("modified_by")
    column_values.append(str(session["id"]))

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

    leaf_selected_rss = this_request.get('leaf_selected_rss', [])
    rss_string = ','.join(leaf_selected_rss)

    # Add the column if it does not exist
    add_column_if_not_exists(mycursor, account_list, "leaf_selected_rss", "TEXT", False)

    mycursor.execute(f"UPDATE {account_list} SET leaf_selected_rss = %s, modified = CURRENT_TIMESTAMP WHERE id = %s", (rss_string, last_row_id))
    mydb.commit()

    for key, val in this_request.items():
        if key.startswith("a-"):
            final_key = key.replace("a-", "")

            if final_key.strip().lower().endswith("id"):
                final_key_to_update_dynamically = final_key
                final_val_to_update_dynamically = val + last_row_id

    if final_key_to_update_dynamically:
        mycursor.execute(f"UPDATE {account_list} SET {final_key_to_update_dynamically} = {final_val_to_update_dynamically}, modified = CURRENT_TIMESTAMP WHERE id = '{last_row_id}'")
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


def get_available_fields(accountId, reference):
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
            columns_info = [(item[0]) for item in columns_info]

            if "year" not in columns_info:
                columns_info.append("year")
            if "month" not in columns_info:
                columns_info.append("month")
            if "day" not in columns_info:
                columns_info.append("day")

            jsonR = {"columns": columns_info}
        else:
            print("Invalid accountId")

    except Exception as e:
        print("get_available_fields model")
        print(e)
    finally:
        mydb.close()
        return jsonify(jsonR)


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


# Define a custom serializer function
def custom_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()  # Serialize datetime objects to ISO format
    raise TypeError("Type not serializable")


def remove_elements_with_content_or_src(html_content, target):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all elements with src attribute or containing target content
    elements_to_remove = []
    for tag in soup.find_all():
        if tag.get('src') == target:
            elements_to_remove.append(tag)
        else:
            for content in tag.contents:
                if isinstance(content, str) and content.strip() == target.strip():
                    elements_to_remove.append(tag)
                    break

    # Remove the target content and its parent if it makes it empty
    for element in elements_to_remove:
        element.extract()

    # Return the modified HTML
    return soup.prettify()


def scrape_list_data(request):
    json_response = {"running": False, "action": "scraping_data"}

    accountId = werkzeug.utils.escape(request.form.get("accountId"))

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:

        list_name = werkzeug.utils.escape(request.form.get("list_name"))

        tableName = f"account_{accountId}_lists_scraping_settings"
        scraping_query = f"SELECT * FROM {tableName} WHERE list=%s"
        values = (list_name,)
        mycursor.execute(scraping_query, values)
        scraping_details = mycursor.fetchone()

        json_response = {"running": True, "action": "scraping_data"}

    except Exception as e:
        print("crawl_list_data model")
        print(e)
    finally:
        mydb.close()
        return jsonify(json_response)


def get_list_scrape_settings(accountId: str, reference: str):
    accountId = werkzeug.utils.escape(accountId)
    reference = werkzeug.utils.escape(reference)

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    json_response = {"scrape_settings": []}

    mydb, mycursor = db_connection()

    try:

        tableName = f"account_{accountId}_lists_scraping_settings"
        scraping_query = f"SELECT * FROM {tableName} WHERE list=%s"
        values = (reference,)
        mycursor.execute(scraping_query, values)
        scraping_details = mycursor.fetchone()

        json_response = {"scrape_settings": scraping_details}

    except Exception as e:
        print("crawl_list_data model")
        print(e)
    finally:
        mydb.close()
        return jsonify(json_response)


def set_list_scrape_settings(request, accountId: str, reference: str):
    """
    Set scrape settings for a specific list in the database.

    Args:
        request (Request): The HTTP request object.
        accountId (str): The account ID associated with the list.
        reference (str): The reference code for the specific list.

    Returns:
        list: A list containing the values that were inserted into the database for scraping.
    """
    col_to_return = []

    accountId = werkzeug.utils.escape(accountId)
    reference = werkzeug.utils.escape(reference)

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        tableName = f"account_{accountId}_lists_scraping_settings"

        if isinstance(int(accountId), int):

            # Create a table if it doesn't exist
            mycursor.execute(f"CREATE TABLE IF NOT EXISTS {tableName} (id INT AUTO_INCREMENT PRIMARY KEY, list VARCHAR(255) DEFAULT NULL, data JSON, created_by INT(11) DEFAULT NULL, created DATETIME NULL DEFAULT CURRENT_TIMESTAMP, modified DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)")

            # Make sure the list is clean
            delete_config_query = f"DELETE FROM {tableName} WHERE list = %s"
            mycursor.execute(delete_config_query, (reference,))
            mydb.commit()

            thisRequest = request.get_json()

            # Insert the data into the table
            mycursor.execute(f"INSERT INTO {tableName} (list, data, created_by) VALUES (%s, %s, %s)", (reference, json.dumps(thisRequest), int(session["id"])))
            mydb.commit()
        else:
            print("Invalid accountId")

    except Exception as e:
        print("set_list_scrape_settings model")
        print(e)
    finally:
        mydb.close()
        return jsonify(col_to_return)


# Main function to scrape pages and save the content in JSON format
def trigger_new_scrape(request):
    accountId = werkzeug.utils.escape(request.form.get("accountId"))

    if not int(accountId) == int(session["accountId"]):
        return jsonify({"error": "Forbidden"}), 403

    mydb, mycursor = db_connection()

    try:
        tableName = f"account_{accountId}_lists_scraping_settings"

        if isinstance(int(accountId), int):

            reference = werkzeug.utils.escape(request.form.get("reference"))

            scraping_query = f"SELECT data FROM {tableName} WHERE list=%s"
            values = (reference,)
            mycursor.execute(scraping_query, values)
            scraping_details = mycursor.fetchone()
            scraping_details = json.loads(unescape_html(scraping_details[0]))

            folders_to_scrape = [folder.strip() for folder in scraping_details.get("s-folders_to_scrape", "").split(",")]
            regex_rules = [folder.strip() for folder in scraping_details.get("s-regex_rules", "").split(",")]

            tableName = f"account_{accountId}_list_{reference}"
            delete_query = f"DELETE FROM {tableName};"
            mycursor.execute(delete_query)
            mydb.commit()

            count_pages = 0

            for folder in folders_to_scrape:
                folder_path = os.path.join(Config.WEBSERVER_FOLDER, folder)
                # current_app.logger.debug(f"Folder: {folder_path}")
                # Check if the folder exists
                if os.path.exists(folder_path):
                    current_app.logger.debug(f"Folder exist: {folder_path}")
                if not os.path.exists(folder_path):
                    print(f"Folder does not exist: {folder_path}")

                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if file.endswith(Config.PAGES_EXTENSION):
                            file_path = os.path.join(root, file)
                            match_rule = True
                            if regex_rules and len(regex_rules) > 0:
                                match_rule = None
                                is_match = True
                                for regex_rule in regex_rules:
                                    if regex_rule != '':
                                        regex_rule = regex_rule.replace('__BACKSLASH__TO_REPLACE_ON_WEB__', '\\')
                                        # Search for the pattern in the URL
                                        this_match = re.search(regex_rule, file_path)
                                        if this_match is None:
                                            is_match = None
                                    else:
                                        match_rule = True

                                if is_match is not None:
                                    match_rule = True

                            if match_rule is not None:
                                html_content = read_html_file(file_path)
                                soup = BeautifulSoup(html_content, 'lxml')
                                page_data = {}

                                for key, selector in scraping_details.items():
                                    if selector == "__found_in_folder__":
                                        data_key = key.replace("scrape__", "")
                                        page_data[data_key] = folder
                                    elif key.startswith("scrape__"):
                                        data_key = key.replace("scrape__", "")
                                        if selector.strip() != "":
                                            content = extract_content(soup, selector)
                                            if content:  # Only add if content is not empty or None
                                                page_data[data_key] = content

                                page_data["modified_by"] = session['id']
                                if page_data:  # Only add the file's data if there's at least one key with content
                                    columns = ', '.join(page_data.keys())
                                    placeholders = ', '.join(['%s'] * len(page_data))
                                    add_data = f"INSERT INTO {tableName} ({columns}) VALUES ({placeholders})"
                                    data_tuple = tuple(page_data.values())
                                    count_pages = count_pages + 1
                                    # current_app.logger.debug(f"Total files to process: {count_pages}")
                                    mycursor.execute(add_data, data_tuple)
                                    mydb.commit()

        else:
            print("Invalid accountId")

    except Exception as e:
        print("trigger_new_scrape model")
        print(e)
        return jsonify({"task": "Adding pages", "status": False})
    finally:
        mydb.close()
        return jsonify({"task": "Adding pages", "status": True})


# Function to read HTML content from a file
def read_html_file(file_path):
    encoding = 'utf-8'
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        # if encoding.strip() != 'utf-8':
        #     current_app.logger.debug(f"Detected encoding in file: {file_path} - {encoding}")

    with open(file_path, 'r', encoding=encoding) as file:
        return file.read()


def extract_and_format(url: str, *pattern_and_format_pairs: Tuple[str, str]) -> str:
    for pattern, output_format in pattern_and_format_pairs:
        match = re.search(pattern, url)

        if match:
            # Create a dictionary of all matched groups
            matched_groups = {f'group{i}': match.group(i) for i in range(1, len(match.groups()) + 1)}

            # Replace format placeholders with the matched group values
            formatted_output = output_format
            for group_name, value in matched_groups.items():
                formatted_output = formatted_output.replace(f'{{{group_name}}}', value)

            return formatted_output
    return "No match found."


# Function to extract content based on the given selector
def extract_content(soup, selector):
    try:
        if '>' in selector and 'ignore' in selector:
            # Split by the last occurrence of '>' to separate base selector and ignore part
            parts = selector.rsplit('>', 1)
            base_selector = parts[0].strip()
            ignore_parts = parts[1].strip()
            ignore_parts = re.search(r'ignore\((.+?)\)', ignore_parts)
            ignore_parts = ignore_parts.group(1)

            # Select the content based on the base selector
            content = extract_content(soup, base_selector)
            if not content:
                return None

            parts = ignore_parts.split(';')
            tag_part = ""
            text_part = ""

            for part in parts:
                if 'tag:' in part:
                    tag_part = part
                if 'text:' in part:
                    text_part = part

            # Lists to store text patterns and tag patterns
            text_patterns = []
            tag_patterns = []

            # Extract tag patterns
            if tag_part:
                tag_patterns = re.findall(r'tag:"(.*?)"', tag_part)
                additional_tags = re.findall(r'",\s*"(.*?)"', tag_part)
                tag_patterns.extend(additional_tags)

            # Extract text patterns
            if text_part:
                text_patterns = re.findall(r'text:"(.*?)"', text_part)
                additional_texts = re.findall(r'",\s*"(.*?)"', text_part)
                text_patterns.extend(additional_texts)

            # Remove text patterns from content
            if len(text_patterns) > 0:
                for pattern in text_patterns:
                    content = content.replace(pattern, "")

            # Remove tag patterns from content
            if len(tag_patterns) > 0:
                soup = BeautifulSoup(content, 'html.parser')
                for tag in tag_patterns:
                    for t in soup.find_all(tag):
                        t.extract()
                content = str(soup)

            return content.strip()

        if '>' in selector and 'regex' in selector:
            # Split by the last occurrence of '>' to separate base selector and regex part
            parts = selector.rsplit('>', 1)
            base_selector = parts[0].strip()
            regex_part = parts[1].strip()
            # Replace the placeholder with actual backslash
            regex_part = regex_part.replace('__BACKSLASH__TO_REPLACE_ON_WEB__', '\\')

            # Extract the regex pattern and format from the regex part
            regex_match = re.search(r'regex\((.+?),\s*(.*?)\)', regex_part)
            # regex_match = re.search(r'regex\(r?"(.+?)",\s*"(.*?)"\)', regex_part)
            if not regex_match:
                raise ValueError(f"Invalid regex format in selector: {selector}")

            pattern = regex_match.group(1)
            output_format = regex_match.group(2)

            # Select the content based on the base selector
            content = extract_content(soup, base_selector)
            if not content:
                return None

            # Apply the regex pattern to the element's content
            match = re.search(pattern, content)

            if match:
                # Create a dictionary of all matched groups
                matched_groups = {f'group{i}': match.group(i) for i in range(1, len(match.groups()) + 1)}
                # Replace format placeholders with the matched group values
                formatted_output = output_format
                for group_name, value in matched_groups.items():
                    formatted_output = formatted_output.replace(f'{{{group_name}}}', value)

                return formatted_output

            return "No match found."

        if selector.endswith('["ALL"]'):
            selector = selector[:-9].strip()  # remove ["ALL"]
            elements = soup.select(selector)
            this_element_attr = ""
            for element in elements:
                this_element_attr = this_element_attr + str(element)
            return this_element_attr

        if selector.endswith('[ALL]'):
            selector = selector[:-7].strip()  # remove [ALL]
            elements = soup.select(selector)
            this_element_attr = ""
            for element in elements:
                this_element_attr = this_element_attr + str(element)
            return this_element_attr

        if '>' in selector and '[' in selector and ']' in selector:
            # Split by the last occurrence of '>'
            parts = selector.rsplit('>', 1)
            base_selector = parts[0].strip()
            attribute_selector = parts[1].strip()
            inside_split = False
            has_split = False

            # Handle cases with attributes
            if '=' in attribute_selector:

                if '.split(' in attribute_selector:
                    has_split = True
                    start = attribute_selector.find('split("') + len('split("')
                    end = attribute_selector.find('")', start)
                    # Extract the substring
                    inside_split = attribute_selector[start:end]

                    # Split the input string at ".split("
                    split_parts = attribute_selector.split('.split(')

                    # The first part is the string before ".split("
                    attribute_selector = split_parts[0]

                attribute_name = attribute_selector.split('[')[-1].split('=')[0].strip()
                attribute_value = attribute_selector.split('[')[-1].split('=')[1].strip(']').strip('"')
                elements = soup.select(base_selector)
                for element in elements:
                    attr_value = element.get(attribute_name)
                    if isinstance(attr_value, list):
                        attr_value = ' '.join(attr_value)
                    if attr_value == attribute_value:
                        if attribute_value == "datePublished":
                            element_to_return = element.get('content')
                        else:
                            element_to_return = element.get('href')
                        if has_split:
                            return element_to_return.split(inside_split)[-1]
                        else:
                            return element_to_return
            else:
                attribute_name = attribute_selector.split('[')[-1].split(']')[0].strip()
                elements = soup.select(base_selector)
                this_element_attr = ""
                for element in elements:
                    if element.get(attribute_name):
                        this_element_attr = element.get(attribute_name)
                return this_element_attr

        if '>' in selector and ']' in selector:
            attribute = selector.split('[')[-1].split(']')[0]
            selector = selector.rsplit('>', 1)[0].strip()
            elements = soup.select(selector)
            this_element_attr = ""
            for element in elements:
                if element.get(attribute):
                    this_element_attr = element.get(attribute)
            return this_element_attr

        else:
            element = soup.select_one(selector.strip())
            return element.decode_contents().strip() if element and not is_only_linebreaks(element.text) else None
            # return element.text.strip() if element and not is_only_linebreaks(element.text) else None
    except Exception as e:
        print(f"Error processing selector '{selector}': {e}")
        return None


def is_only_linebreaks(s):
    # Strip all whitespace characters including newlines
    stripped_string = s.strip()
    # Check if the resulting string is empty
    return stripped_string == ''


# Function to unescape HTML entities
def unescape_html(html):
    return (html.replace('&gt;', '>')
            .replace('&lt;', '<')
            .replace('&quot;', '"')
            .replace('&#39;', "'")
            .replace('&amp;', '&')
            .replace('&comma;', ','))
