# models.py
from leaf import decorators


def get_deployments():
    """
    Fetch deployments from the database.

    Returns:
        list: List of deployments fetched from the database.
    """
    # Get a database connection
    mydb, mycursor = decorators.db_connection()
    # Execute the SQL query to fetch deployments
    mycursor.execute("SELECT deployment_number, deployment_user, submitted_timestamp, source_files, destination_location, completed_timestamp, status, deployment_log FROM deployments")
    # Fetch all the rows
    deployments = mycursor.fetchall()
    deployments = [
        {
            "deployment_number": deployment[0],
            "deployment_user": deployment[1],
            "submitted_timestamp": deployment[2],
            "source_files": deployment[3],
            "destination_location": deployment[4],
            "completed_timestamp": deployment[5],
            "status": deployment[6],
            "deployment_log": deployment[7],
        }
        for deployment in deployments
    ]
    # Close the database connection
    mydb.close()
    return deployments
