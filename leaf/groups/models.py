from leaf import decorators


def get_account_groups(account_id):
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


def get_user_groups(user_id):
    """
    Fetches the groups associated with a given user ID from the database.

    This function connects to the database, executes a query to retrieve the groups
    that the specified user belongs to, and returns a dictionary containing
    the group IDs and names.

    Args:
        user_id (int): The ID of the user whose groups are to be fetched.

    Returns:
        list: A dict represents a group with the group's ID as the key and the group's name as the value.
    """

    # Get a database connection
    mydb, mycursor = decorators.db_connection()

    try:
        # Fetch the user groups
        query = """
        SELECT user_groups.group_id, user_groups.group_name
        FROM group_member
        JOIN user_groups ON group_member.group_id = user_groups.group_id
        WHERE group_member.user_id = %s;
        """

        mycursor.execute(query, (user_id,))
        groups = {group_id: group_name for group_id, group_name in mycursor.fetchall()}
        return groups

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        raise RuntimeError(f"An error occurred while fetching user groups: {str(e)}")
    finally:
        if mydb:
            mydb.close()
