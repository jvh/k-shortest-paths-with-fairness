import sqlite3


class Database2:
    DATABASE_LOCATION = '/Volumes/DATA/sumo_routes/bournemouth_100/bournemouth_1_hours_fairness.sqlite'

    def __init__(self):
        Database2.conn = sqlite3.connect(self.DATABASE_LOCATION)
        Database2.conn.row_factory = lambda cursor, row: row[0]
        Database2.cursor = Database2.conn.cursor()

    @staticmethod
    def getAllTables():
        """
        Gets the table names for all tables present in the database

        Return:
            [str]: The names of all of the tables
        """
        # Stores the table names held in tuples
        tableNamesUnformatted = Database2.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        # Stores all the table names
        tableNamesFormatted = []
        for table in tableNamesUnformatted:
            # Correcting the format of the string (converted from a tuple) to be suitable
            tableNamesFormatted.append(str(table).replace("'", "").replace("(", "").replace(")", "").replace(",", ""))

        return tableNamesFormatted


    @staticmethod
    def getDBTableContents(tableName):
        """
        Puts the rows of a table into a list
        Args:
            tableName (str): The table
        Returns:
            entries (str[]): List containing the table contents
        """
        entries = Database2.cursor.execute('SELECT * FROM {}'.format(tableName)).fetchall()
        return entries

    @staticmethod
    def getMeanSpeed(tableName):
        id_list = Database2.getAllUniqueIDs(tableName)

        new = {}

        for id in id_list:
            lengths = Database2.cursor.execute("SELECT tripinfo_routeLength FROM {} WHERE tripinfo_id = '{}'".
                                               format(tableName, id)).fetchall()
            times = Database2.cursor.execute("SELECT tripinfo_duration FROM {} WHERE tripinfo_id = '{}'".
                                   format(tableName, id)).fetchall()

            total_length = sum(lengths)
            total_time = sum(times)

            speed = total_length/total_time

            new[id] = speed

        return new

    @staticmethod
    def getAllRouteTaken(tableName):
        id_list = Database2.getAllUniqueIDs(tableName)
        # Stores the id: [routeLength]
        idRouteLength = {}

        new = {}

        for id in id_list:
            lengths = Database2.cursor.execute("SELECT tripinfo_routeLength FROM {} WHERE tripinfo_id = '{}'".
                                               format(tableName, id)).fetchall()
            times = Database2.cursor.execute("SELECT tripinfo_duration FROM {} WHERE tripinfo_id = '{}'".
                                   format(tableName, id)).fetchall()

            tempLarger = []
            for x in range(len(times)):
                temp = []
                temp.append(times[x])
                temp.append(lengths[x])
                tempLarger.append(temp)
            new[id] = tempLarger


            idRouteLength[id] = lengths
        return new


    @staticmethod
    def getMeanForEachVehicleIndividual(tablename):
        vehicleData = Database2.getAllRouteTaken(tablename)
        meanVehicleSpeed = {}
        for key, values in vehicleData.items():
            temp = []
            for value in values:
                time = value[0]
                length = value[1]
                speed = float(length)/float(time)
                temp.append(speed)
            meanVehicleSpeed[key] = temp
        return meanVehicleSpeed

    @staticmethod
    def getAllUniqueIDs(tableName):
        entries = Database2.cursor.execute('SELECT DISTINCT tripinfo_id FROM {}'.format(tableName)).fetchall()
        return entries

if __name__ == '__main__':
    db = Database2()
    for table in db.getAllTables():
        print(table)
        print(db.getMeanForEachVehicle(table))
        # id_list = db.getAllUniqueIDs(table)
        # for id in id_list:
        #     print(id)
        #     print(db.getAllRouteTaken(table, id))
        # print(data3)

