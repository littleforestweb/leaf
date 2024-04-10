from flask import session

from leaf.decorators import db_connection


def get_users_data():
    """
    Retrieve user data from the database.

    Returns:
        list: List of dictionaries containing user information.
    """
    mydb, mycursor = db_connection()

    try:
        # Execute SQL query to fetch user data
        mycursor.execute("SELECT user.id, user.username, user.email FROM user")

        # Extract user data and create a list of dictionaries
        users_list = [{"id": user[0], "name": user[1], "email": user[2]} for user in mycursor.fetchall()]

        return users_list

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        raise RuntimeError(f"An error occurred while fetching users: {str(e)}")
    finally:
        if mydb:
            mydb.close()


def add_user_to_database(username, email, is_admin, password):
    """
    Add a new user to the database.

    Args:
        username (str): User's name.
        email (str): User's email.
        is_admin (str): User's master status.
        password (str): User's password.

    Returns:
        bool: True if the user is added successfully, False otherwise.
    """

    mydb, mycursor = db_connection()

    try:
        # Run SQL Command to insert the new user
        mycursor.execute("INSERT INTO user (username, email, is_admin, account_id, password) VALUES (%s, %s, %s, %s, %s)", (username, email, is_admin, session["accountId"], password))
        mydb.commit()

        return True

    except Exception as e:
        # Log the error or handle it appropriately
        print(f"Error in add_user_to_database: {e}")
        return False
    finally:
        # Always close the database connection
        if mydb:
            mydb.close()


def update_user_in_database(original_user_name, new_user_name, new_user_email, new_user_display_name):
    """
    Update user information in the database.

    Args:
        original_user_name (str): Original name of the user to update.
        new_user_name (str): New name for the user.
        new_user_email (str): New email for the user.
        new_user_display_name (str): New display name for the user.

    Returns:
        bool: True if the user is updated successfully, False otherwise.
    """
    mydb, mycursor = db_connection()

    try:
        # Run SQL Command to update the user
        update_users_query = "UPDATE user SET name=%s, email=%s, display_name=%s WHERE name=%s"
        values = (new_user_name, new_user_email, new_user_display_name, original_user_name)

        mycursor.execute(update_users_query, values)
        mydb.commit()

        return True

    except Exception as e:
        # Log the error or handle it appropriately
        print(f"Error in update_user_in_database: {e}")
        return False

    finally:
        # Always close the database connection
        if mydb:
            mydb.close()


def delete_users_from_database(usernames):
    """
    Delete users from the database.

    Args:
        usernames (list): List of usernames to be deleted.

    Returns:
        bool: True if users are deleted successfully, False otherwise.
    """
    mydb, mycursor = db_connection()

    try:
        # Run SQL Command to delete users
        placeholders = ','.join(['%s'] * len(usernames))
        delete_users_cmd = f"DELETE FROM user WHERE name IN ({placeholders})"
        mycursor.execute(delete_users_cmd, usernames)
        mydb.commit()

        return True

    except Exception as e:
        # Log the error or handle it appropriately
        print(f"Error in delete_users_from_database: {e}")
        return False

    finally:
        # Always close the database connection
        if mydb:
            mydb.close()
