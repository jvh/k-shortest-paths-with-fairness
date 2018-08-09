###################################################################################################################
# Using SQLite3 to store information to a database in which the results of the simulation are stored              #
#                                                                                                                 #
# Author: Jonathan Harper                                                                                         #
###################################################################################################################

__author__ = "Jonathan Harper"

###########
# IMPORTS #
###########

import sqlite3

from src.code import SumoConnection as sumo
from src.code import RoutingFunctions as func
from src.code import SimulationFunctions as sim

#############
# VARIABLES #
#############

VEHICLE_OUTPUT_TABLE = "vehicle_output"
SIMULATION_OUTPUT_TABLE = "simulation_output"


class Database:
    """
    This is where the database and its corresponding tables are defined.
    """

    def __init__(self):
        Database.conn = sqlite3.connect(sumo.DATABASE_LOCATION)
        Database.cursor = Database.conn.cursor()

        try:
            # Creates a net table called 'vehicle_output' storing the vehicleID in the first column as a primary key
            Database.cursor.execute('CREATE TABLE {} (vehicleID INTEGER PRIMARY KEY)'.format(VEHICLE_OUTPUT_TABLE))
            # Adding in the column 'numberTimesRerouted'
            Database.cursor.execute("ALTER TABLE {} ADD COLUMN 'numberTimesRerouted' INTEGER"
                                    .format(VEHICLE_OUTPUT_TABLE))
            # Adding in the column 'cumulativeExtraTime'
            Database.cursor.execute("ALTER TABLE {} ADD COLUMN 'cumulativeExtraTime' INTEGER"
                                    .format(VEHICLE_OUTPUT_TABLE))
            # Adding in the column 'totalTimeSpentInSystem'
            Database.cursor.execute("ALTER TABLE {} ADD COLUMN 'totalTimeSpentInSystem' REAL"
                                    .format(VEHICLE_OUTPUT_TABLE))
        except sqlite3.OperationalError:
            print("Table \'{}\' already created".format(VEHICLE_OUTPUT_TABLE))

        try:
            # Creates a net table called 'simulation_output' storing the timestep, the simulation number, and the
            # corresponding information
            Database.cursor.execute('CREATE TABLE {} (simIndexTimestep String PRIMARY KEY)'
                                    .format(SIMULATION_OUTPUT_TABLE))
            Database.cursor.execute("ALTER TABLE {} ADD COLUMN 'fairnessIndex' REAL"
                                    .format(SIMULATION_OUTPUT_TABLE))
            Database.cursor.execute("ALTER TABLE {} ADD COLUMN 'standardDeviationQOE' REAL"
                                    .format(SIMULATION_OUTPUT_TABLE))
            Database.cursor.execute("ALTER TABLE {} ADD COLUMN 'meanCongestionLevel' REAL"
                                    .format(SIMULATION_OUTPUT_TABLE))
        except sqlite3.OperationalError:
            print("Table \'{}\' already created".format(SIMULATION_OUTPUT_TABLE))

    @staticmethod
    def populateDBVehicleTable():
        """
        Populates the DB with information regarding the finished simulation
        """
        for vehicle in func.vehicleReroutedAmount:
            # # Updates the values for the given vehicleID if it already exists, otherwise insert into the DB
            Database.cursor.execute(
                "INSERT OR REPLACE INTO {table} (vehicleID, numberTimesRerouted, cumulativeExtraTime, "
                "totalTimeSpentInSystem) "
                "VALUES ({vehicleID}, COALESCE({reroutedAmount}, '{reroutedAmount}'), "
                "COALESCE({extraTimeAddition}, '{extraTimeAddition}'), "
                "COALESCE({totalTime}, '{totalTime}'))"
                .format(table=VEHICLE_OUTPUT_TABLE,
                        vehicleID=vehicle,
                        rerouteAddition=func.vehicleReroutedAmount[vehicle],
                        reroutedAmount=func.vehicleReroutedAmount[vehicle],
                        extraTimeAddition=func.cumulativeExtraTime[vehicle],
                        totalTime=sim.timeSpentInNetwork[vehicle]))

        # Commits any changes made to the database
        Database.conn.commit()

    @staticmethod
    def populateDBSimulationTable(i, fairnessIndex, sd, simulationIndex, meanCongestion):
        """
        Populates the DB with information regarding the finished simulation

        Args:
            i (int): The timestep
            fairnessIndex (float): The fairness index of the QOE's
            sd (float): The standard deviations of the QOE's
            simulationIndex (str): The index of the simulation (number and corresponding type)
            meanCongestion (float): This is the % of congestion in the road network
        """
        simIndex = str(simulationIndex + str(i))

        Database.cursor.execute(
            "INSERT OR REPLACE INTO {table} (simIndexTimestep, fairnessIndex, standardDeviationQOE, "
            "meanCongestionLevel) "
            "VALUES ('{index}', "
            "COALESCE({fairness}, '{fairness}'), "
            "COALESCE({standard}, '{standard}'), "
            "COALESCE({congestion}, '{congestion}'))"
                .format(
                    table=SIMULATION_OUTPUT_TABLE,
                    index=simIndex,
                    fairness=fairnessIndex,
                    standard=sd,
                    congestion=meanCongestion))
        # Commits any changes made to the database
        Database.conn.commit()

    @staticmethod
    def closeDB():
        """
        Closes the database
        """
        # Closes the connection to the database
        Database.conn.close()

    @staticmethod
    def getAllTables():
        """
        Gets the table names for all tables present in the database

        Return:
            [str]: The names of all of the tables
        """
        # Stores the table names held in tuples
        tableNamesUnformatted = Database.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        # Stores all the table names
        tableNamesFormatted = []
        for table in tableNamesUnformatted:
            # Correcting the format of the string (converted from a tuple) to be suitable
            tableNamesFormatted.append(str(table).replace("'", "").replace("(", "").replace(")", "").replace(",", ""))

        return tableNamesFormatted

    def clearDB(self):
        """
        Clears all tables in the DB
        """
        tableNames = self.getAllTables()

        for table in tableNames:
            self.clearTable(table)

    @staticmethod
    def getDBTableContents(tableName):
        """
        Puts the rows of a table into a list
        Args:
            tableName (str): The table
        Returns:
            entries (str[]): List containing the table contents
        """
        entries = Database.cursor.execute('SELECT * FROM {}'.format(tableName)).fetchall()
        return entries

    def fairnessMetricsIntoDictionary(self):
        """
        Puts the rows of a table into a list
        Returns:
            {vehicleID (str): fairnessMetrics str[]): Returns a dictionary containing the vehicleID: fairnessMetrics
        """
        entries = self.getDBTableContents(VEHICLE_OUTPUT_TABLE)

        # Stores a dictionary of all of the entries from the database, with the key being the vehicleID and the values
        # being a list of the fairness metrics from the database
        entryDict = {}
        for entry in entries:
            # set vehicleID as the key and the fairness metrics as the values (stored in a list)
            entryDict[entry[0]] = entry[1:]

        return entryDict

    @staticmethod
    def clearTable(tableName):
        """
        Clears a single table from the database

        Args:
            tableName (str): The table to clear
        """
        Database.cursor.execute("DELETE FROM {}".format(tableName))
        Database.conn.commit()
