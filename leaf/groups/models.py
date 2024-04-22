from flask import session

from leaf import decorators


def get_groups():
    """
    Fetch groups from the database.

    Returns:
        list: List of groups fetched from the database.
    """

    # Get a database connection
    mydb, mycursor = decorators.db_connection()

    # Execute the SQL query to fetch groups
    query = "SELECT group_id, group_name, created_date, modified_date FROM user_groups where user_groups.account_id = %s"
    values = (str(session["accountId"]),)
    # Execute the SQL query to fetch groups
    mycursor.execute(query, values)

    # Fetch all the rows
    groups = mycursor.fetchall()
    groups = [{"id": group[0], "group_name": group[1], "created_date": group[2], "modified_date": group[3]} for group in groups]

    # Close the database connection
    mydb.close()
    return groups

def get_all_user_groups(account_id):
    """
    Fetch groups from the database.

    Returns:
        list: List of groups fetched from the database.
    """

    # Get a database connection
    mydb, mycursor = decorators.db_connection()

    query = "SELECT group_id, group_name FROM user_groups where user_groups.account_id = %s"
    values = (account_id,)
    # Execute the SQL query to fetch groups
    mycursor.execute(query, values)

    # Fetch all the rows
    groups = mycursor.fetchall()
    groups = {group[1]: group[0] for group in groups}

    # Close the database connection
    mydb.close()
    return groups
