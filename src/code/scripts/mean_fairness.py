import sqlite3


class Database2:
    DATABASE_LOCATION = '/Users/jonathan/Desktop/final_results/luton_fairness/fairness/luton_2_hours_fairness.sqlite'

    def __init__(self):
        Database2.conn = sqlite3.connect(self.DATABASE_LOCATION)
        # Database2.conn.row_factory = lambda cursor, row: row[0]
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

    @staticmethod
    def calculateMeanFairness():
        entries = Database2.cursor.execute('SELECT * FROM simulation_output').fetchall()
        return entries


if __name__ == '__main__':
    SCENARIO = 'luton'
    ALGORITHM = 3
    ALGO = ''

    if ALGORITHM == 0:
        ALGO= 'noRerouting'
    elif ALGORITHM == 1:
        ALGO = 'DSP'
    elif ALGORITHM == 2:
        ALGO = 'kPaths'
    elif ALGORITHM == 3:
        ALGO = 'fairness'

    db = Database2()

    print(db.calculateMeanFairness())
    entryDict = {}

    for entry in db.calculateMeanFairness():
        entryDict[entry[0]] = entry[1:]

    fairness_sim = {}
    fairness = []

    for i in range(15):
        x = i+1
        for y in range(20):
            u = y+1
            try:
                step = u * 100
                sim_step = '{}_2_hours_{}_{}_{}'.format(SCENARIO, ALGO, x, step)
                value = entryDict[sim_step][0]
                if value < 1 and value > 0.6:
                    fairness.append(value)
            except Exception:
                print("No more indexes")

        if fairness:
            fairness_sim[x] = sum(fairness)/len(fairness)
            fairness = []

    print(fairness_sim)

    print()
    new_str = ''

    for fair in fairness_sim:
        new_str += str('({}, {})\n'.format(fair, fairness_sim[fair]))

    print(new_str)

