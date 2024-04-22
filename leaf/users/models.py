from flask import session

from leaf import Config
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
        mycursor.execute("SELECT user.id, user.username, user.email, is_admin, is_manager FROM user")

        # Extract user data and create a list of dictionaries
        users_list = [{"id": user[0], "name": user[1], "email": user[2], "is_admin": user[3], "is_manager": user[4]} for user in mycursor.fetchall()]

        return users_list

    except Exception as e:
        # Log the exception or handle it as appropriate for your application
        raise RuntimeError(f"An error occurred while fetching users: {str(e)}")
    finally:
        if mydb:
            mydb.close()


def add_user_to_database(username, email, is_admin, is_manager, password):
    """
    Add a new user to the database.

    Args:
        username (str): User's name.
        email (str): User's email.
        is_admin (int): User's admin status.
        is_manager (int): User's master status.
        password (str): User's password.

    Returns:
        bool: True if the user is added successfully, False otherwise.
    """

    mydb, mycursor = db_connection()

    try:
        # Run SQL Command to insert the new user
        mycursor.execute("INSERT INTO user (username, email, is_admin, is_manager, account_id, password) VALUES (%s, %s, %s, %s, %s, %s)", (username, email, is_admin, is_manager, session["accountId"], password))
        user_id = mycursor.lastrowid

        # Add to Admin Group
        if is_admin == 1:
            mycursor.execute("SELECT group_id FROM user_groups WHERE group_name = %s", (Config.POWER_USER_GROUP,))
            admin_group_id = mycursor.fetchone()[0]
            mycursor.execute("INSERT INTO group_member (group_id, user_id) VALUES (%s, %s)", (admin_group_id, user_id))

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


def edit_user_to_database(user_id, is_admin, is_manager):
    """
    Edit a user in the database.

    Args:
        user_id (int): User's ID.
        is_admin (int): User's admin status.
        is_manager (int): User's manager status.

    Returns:
        bool: True if the user is edited successfully, False otherwise.
    """

    mydb, mycursor = db_connection()

    try:
        # Run SQL Command to update the user
        mycursor.execute("UPDATE user SET is_admin = %s, is_manager = %s WHERE id = %s", (is_admin, is_manager, user_id))

        # Add to Admin Group
        if is_admin == 1:
            mycursor.execute("SELECT group_id FROM user_groups WHERE group_name = %s", (Config.POWER_USER_GROUP,))
            admin_group_id = mycursor.fetchone()[0]
            mycursor.execute("INSERT INTO group_member (group_id, user_id) VALUES (%s, %s)", (admin_group_id, user_id))

        mydb.commit()
        return True

    except Exception as e:
        # Log the error or handle it appropriately
        print(f"Error in edit_user_to_database: {e}")
        return False
    finally:
        # Always close the database connection
        if mydb:
            mydb.close()


def delete_user_to_database(user_id):
    """
    Delete a user from the database.

    Args:
        user_id (int): User's ID.

    Returns:
        bool: True if the user is deleted successfully, False otherwise.
    """

    mydb, mycursor = db_connection()

    try:
        # Run SQL Command to delete the user
        mycursor.execute("DELETE FROM user WHERE user.id = %s", (user_id,))
        mydb.commit()
        return True

    except Exception as e:
        # Log the error or handle it appropriately
        print(f"Error in delete_user_to_database: {e}")
        return False
    finally:
        # Always close the database connection
        if mydb:
            mydb.close()
