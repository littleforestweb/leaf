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

    # Execute the SQL query to fetch deployments
    mycursor.execute(f"SELECT group_id, group_name, created_date, modified_date FROM user_groups where user_groups.account_id = {session["accountId"]}")

    # Fetch all the rows
    groups = mycursor.fetchall()
    groups = [{"id": group[0], "group_name": group[1], "created_date": group[2], "modified_date": group[3]} for group in groups]

    # Close the database connection
    mydb.close()
    return groups
