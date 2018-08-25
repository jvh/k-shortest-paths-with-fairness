import pandas as pd
import sqlite3

class Database3:
    def __init__(self, database):
        Database3.conn = sqlite3.connect(database)
        Database3.cursor = Database3.conn.cursor()

    @staticmethod
    def getDBTableContents(tableName):
        entries = Database3.cursor.execute('SELECT * FROM {}'.format(tableName)).fetchall()

        entryDict = {}
        for entry in entries:
            entryDict[entry[0]] = entry[1:]

        return entryDict, entries

def create_data_frame(dict_to_process):
    data_frame = pd.DataFrame.from_records([dict_to_process])
    return data_frame

def returnAtIndex(dict, index):
    new_dict = {}
    for entry in dict:
        new_dict[entry] = dict[entry][index]

    return new_dict

def returnCum(dict, index):
    new_dict = {}
    for entry in dict:
        new_dict[entry] = dict[entry][1]

    return new_dict

if __name__ == '__main__':
    fairness = False

    kPaths = True
    dsp = False
    noRerouting = False

    fairness_table = '/Users/jonathan/Desktop/final_results/luton_fairness/fairness/luton_2_hours_fairness.sqlite'
    kpaths_table = '/Users/jonathan/Desktop/final_results/luton_fairness/kPaths/luton_2_hours_kPaths.sqlite'
    dsp_table = '/Users/jonathan/Desktop/final_results/bournemouth_fairness/DSP/bournemouth_2_hours_DSP.sqlite'
    norerouting_table = '/Volumes/DATA/sumo_routes/bournemouth_100/bournemouth_1_hours_noRerouting.sqlite'


    ############
    # FAIRNESS #
    ############

    if fairness:
        db = Database3(fairness_table)

        entryDict, entries = db.getDBTableContents('vehicle_output')

        # Rerouting
        reroutingDict = returnAtIndex(entryDict, 0)
        only_rerouting = reroutingDict.values()

        # Cumulative
        cumulative = returnAtIndex(entryDict,1)
        cumulative_only = cumulative.values()

        print('fairness')

        print(only_rerouting)
        print(cumulative_only)

        print()

    ##########
    # KPATHS #
    ##########

    if kPaths:
        db = Database3(kpaths_table)

        entryDict, entries = db.getDBTableContents('vehicle_output')

        # Rerouting
        reroutingDict = returnAtIndex(entryDict, 0)
        only_rerouting = reroutingDict.values()

        # Cumulative
        cumulative = returnAtIndex(entryDict, 1)
        cumulative_only = cumulative.values()

        print('kPaths')

        print(only_rerouting)
        print(cumulative_only)

        print()

    #######
    # DSP #
    #######

    if dsp:
        db = Database3(dsp_table)

        entryDict, entries = db.getDBTableContents('vehicle_output')

        # Rerouting
        reroutingDict = returnAtIndex(entryDict, 0)
        only_rerouting = reroutingDict.values()

        # Cumulative
        cumulative = returnAtIndex(entryDict, 1)
        cumulative_only = cumulative.values()

        print('DSP')

        print(only_rerouting)
        print(cumulative_only)

        print()

    ###############
    # NO-REROUTING #
    ###############

    if noRerouting:
        db = Database3(norerouting_table)

        entryDict, entries = db.getDBTableContents('vehicle_output')

        # Rerouting
        reroutingDict = returnAtIndex(entryDict, 0)
        only_rerouting = reroutingDict.values()

        # Cumulative
        cumulative = returnAtIndex(entryDict, 1)
        cumulative_only = reroutingDict.values()

        print('no-rerouting')

        print(only_rerouting)
        print(cumulative_only)

        print()