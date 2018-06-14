import sqlite3

import itertools

from src.project.code import SumoConnection as sumo
from src.project.code import RoutingAlgorithms as routing
from src.project.code import RoutingFunctions as func
from src.project.code import Testing as testing
from src.project.code import InitialMapHelperFunctions as initialFunc
from src.project.code import SimulationFunctions as sim

__author__ = "Jonathan Harper"

"""
Using SQLite3 to store information to a database in which the results of the simulation are stored
"""

VEHICLE_OUTPUT_TABLE = "vehicle_output"
SIMULATION_OUTPUT_TABLE = "simulation_output"



class Database:

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
            # Creates a net table called 'simulation_output' storing the timestep, the simulation number, and the corresponding information
            Database.cursor.execute('CREATE TABLE {} (simIndexTimestep String PRIMARY KEY)'.format(SIMULATION_OUTPUT_TABLE))
            Database.cursor.execute("ALTER TABLE {} ADD COLUMN 'fairnessIndex' REAL"
                                    .format(SIMULATION_OUTPUT_TABLE))
            Database.cursor.execute("ALTER TABLE {} ADD COLUMN 'standardDeviationQOE' REAL"
                                    .format(SIMULATION_OUTPUT_TABLE))
        except sqlite3.OperationalError:
            print("Table \'{}\' already created".format(SIMULATION_OUTPUT_TABLE))

    def populateDBVehicleTable(self):
        """
        Populates the DB with information regarding the finished simulation
        """
        for vehicle in func.vehicleReroutedAmount:
            # # Updates the values for the given vehicleID if it already exists, otherwise insert into the DB
            # Database.cursor.execute("INSERT OR REPLACE INTO {table} (vehicleID, numberTimesRerouted, cumulativeExtraTime, ) VALUES "
            #                         "({vehicleID}, COALESCE({reroutedAmount}, '{reroutedAmount}'))"
            #                         .format(table=VEHICLE_OUTPUT_TABLE, vehicleID=vehicle, rerouteAddition=func.vehicleReroutedAmount[vehicle],
            #                                 reroutedAmount=func.vehicleReroutedAmount[vehicle]))
            # Updates the values for the given vehicleID if it already exists, otherwise insert into the DB
            # Database.cursor.execute("INSERT OR REPLACE INTO {table} (vehicleID, numberTimesRerouted, cumulativeExtraTime, totalTimeSpentInSystem) VALUES "
            #                         "({vehicleID}, COALESCE({reroutedAmount}, '{reroutedAmount}'), COALESCE({extraTimeAddition}, '{extraTimeAddition}'))"
            #                         .format(table=VEHICLE_OUTPUT_TABLE, vehicleID=vehicle, rerouteAddition=func.vehicleReroutedAmount[vehicle],
            #                                 reroutedAmount=func.vehicleReroutedAmount[vehicle], extraTimeAddition=func.cumulativeExtraTime[vehicle]))
            Database.cursor.execute(
                "INSERT OR REPLACE INTO {table} (vehicleID, numberTimesRerouted, cumulativeExtraTime, totalTimeSpentInSystem) VALUES "
                "({vehicleID}, COALESCE({reroutedAmount}, '{reroutedAmount}'), COALESCE({extraTimeAddition}, '{extraTimeAddition}'), COALESCE({totalTime}, '{totalTime}'))"
                .format(table=VEHICLE_OUTPUT_TABLE, vehicleID=vehicle, rerouteAddition=func.vehicleReroutedAmount[vehicle],
                        reroutedAmount=func.vehicleReroutedAmount[vehicle],
                        extraTimeAddition=func.cumulativeExtraTime[vehicle], totalTime=sim.timeSpentInNetwork[vehicle]))

        # for vehicle in sim.timeSpentInNetwork:
        #     # Database.cursor.execute("INSERT OR REPLACE INTO {table} WHERE vehicleID = {vehicleID} (totalTimeSpentInSystem) VALUES "
        #     #                         "(COALESCE({totalTimeSpentInSystem}, '{totalTimeSpentInSystem}'))"
        #     #                         .format(vehicleID=vehicle, table=VEHICLE_OUTPUT_TABLE, totalTimeSpentInSystem=sim.timeSpentInNetwork[vehicle]))
        #     Database.cursor.execute("UPDATE {table} SET totalTimeSpentInSystem = {totalTime} WHERE vehicleID = {vehicleID}".format(
        #         table=VEHICLE_OUTPUT_TABLE, totalTime=sim.timeSpentInNetwork[vehicle], vehicleID=vehicle
        #     ))

        # This is assuming that the database values are not loaded into the corresponding variables before simulation
        # start
        """
        Database.cursor.execute(
            "INSERT OR REPLACE INTO {table} (vehicleID, numberTimesRerouted, cumulativeExtraTime) VALUES "
            "({vehicleID}, COALESCE((SELECT numberTimesRerouted FROM {table} WHERE vehicleId "
            "= {vehicleID}) + {rerouteAddition}, '{reroutedAmount}'), COALESCE((SELECT "
            "cumulativeExtraTime FROM {table} WHERE vehicleId = {vehicleID}) + {extraTimeAddition}, '{extraTimeAddition}'))"
            .format(table=VEHICLE_OUTPUT_TABLE, vehicleID=vehicle, rerouteAddition=func.vehicleReroutedAmount[vehicle],
                    reroutedAmount=func.vehicleReroutedAmount[vehicle],
                    extraTimeAddition=func.cumulativeExtraTime[vehicle]))
        """

        # Commits any changes made to the database
        Database.conn.commit()

    def populateDBSimulationTable(self, i, fairnessIndex, sd, simulationIndex):
        """
        Populates the DB with information regarding the finished simulation

        Args:
            i (int): The timestep
            fairnessIndex (float): The fairness index of the QOE's
            sd (float): The standard deviations of the QOE's
            simulationIndex (str): The index of the simulation (number and corresponding type)
        """
        simIndex = str(simulationIndex + "_" + str(i))

        Database.cursor.execute(
            "INSERT OR REPLACE INTO {table} (simIndexTimestep, fairnessIndex, standardDeviationQOE) VALUES "
            "('{index}', COALESCE({fairness}, '{fairness}'), COALESCE({standard}, '{standard}'))"
            .format(table=SIMULATION_OUTPUT_TABLE, index=simIndex, fairness=fairnessIndex, standard=sd))
        # Commits any changes made to the database
        Database.conn.commit()

    def closeDB(self):
        """
        Closes the database
        """
        # Closes the connection to the database
        Database.conn.close()

    def getAllTables(self):
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

    def getDBTableContents(self, tableName):
        """
        Puts the rows of a table into a list
        Args:
            tableName (str): The table
            id (str): The unique identification (primary key) for a tuple in a table??????
        Returns:
            entries (str[]): List containing the table contents
        """
        # key = Database.cursor.execute('SELECT {} FROM {}'.format(id, tableName)).fetchall()
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

    def clearTable(self, tableName):
        """
        Clears a single table from the database

        Args:
            tableName (str): The table to clear
        """
        Database.cursor.execute("DELETE FROM {}".format(tableName))
        Database.conn.commit()