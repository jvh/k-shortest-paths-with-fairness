import collections
from collections import OrderedDict
from operator import itemgetter

import numpy as np
import sys
import traci

from src.project.code import SumoConnection

SumoConnection
from src.project.code import SumoConnection as sumo
from src.project.code import RoutingFunctions as func
from src.project.code import InitialMapHelperFunctions as initialFunc

__author__ = "Jonathan Harper"

"""
This file contains functions which return information regarding the simulation during runtime.

Can be thought of as 'getters' options during the simulation runtime
"""

# This contains data concerning if the vehicle was in a 'stopped' state (not defined as waiting, e.g. waiting at a
# traffic light) in the last rerouting period. vehicle: stoppedState (for last rerouting period)
stoppedStateLastPeriod = {}
# This holds the total amount of time spent in the system (in terms of complete rerouting periods in which the vehicle
# has been present in the system), in the form {vehicle: totalTimeSpent}
timeSpentInNetwork = {}
# This holds the approximate time each vehicle was in the 'stopped' state, vehicle:time
timeSpentStopped = {}
# This holds the initial time spent in the simulation for each vehicle when the simulation begins. This is not updated
# for the duration of the simulation, it serves its purpose by tracking, at the time of simulation start, the initial
# time spent metrics
initialTimeSpentInNetwork = {}
# Time of arrival at destination (in terms of timesteps) for each vehicle, vehicle:timeOfArrival
arrivalTime = {}
# Time of departure (when the vehicle first arrives) of each vehicle, vehicle:timeEnteredIntoSystem
departureTime = {}
# Stores a list of all vehicles in network currently
vehiclesInNetwork = []

# The maximum amount an edge can vary from the free flow travel time speed until considered an issue
FREE_FLOW_TRAVEL_TIME_MAXIMUM = 5

def returnCongestionLevelEdge(edgeID):
    """
    Gives the congestion level of the edge

    Args:
        edgeID (str): The ID of the edge
    Return:
         float: The occupancy (congestion) of the road, in percentage
    """
    return traci.edge.getLastStepOccupancy(edgeID)


def returnCongestionLevelLane(laneID):
    """
    Gives the congestion level of the road, laneID

    Args:
        laneID (str): The ID of the lane (road)
    Return:
         float: The occupancy (congestion) of the road, in percentage
    """
    return traci.lane.getLastStepOccupancy(laneID)

def getEdgeOneAheadVehicleRoute(vehID):
    """
    Returns the edge in which the given vehicle shall travel to next (the edge after it's current edge in it's route)

    Args:
        vehID (str): The ID of the vehicle
    Return:
         nextEdge (str): The next edge in the vehicle's route
    """
    # Getting the current location of the vehicle
    actualLocation = traci.vehicle.getLaneID(vehID)
    edgeLoc = initialFunc.lanesNetwork[actualLocation]
    # Getting the edge which appears in the route after it's current edge (adding 1 to the index of the
    # current location)
    nextEdge = traci.vehicle.getRoute(vehID)[traci.vehicle.getRoute(vehID).index(edgeLoc) + 1]

    return nextEdge

def getEdge2DCoordinates(edge):
    """
    Gets the 2D coordinates of the 'from' node which connects to the lane

    Args:
        edge (str): The edge to teleport to
    Returns:
        (str, str): Returns the tuple (x, y)
            Individual elements can be accessed by tuple.x and tuple.y
    """
    # Getting them 'from' node associated with that edge
    node = sumo.net.getEdge(edge).getFromNode().getID()
    # Getting the 2D coordinates (x, y) for that node
    x, y = sumo.net.getNode(node).getCoord()
    # Changes the GUI offset to the coordinates of the node
    traci.gui.setOffset("View #0", x, y)
    # print("Edge {} has congestion level {}".format(edge, returnCongestionLevelEdge(edge)))

    # Creating a named tuple to store (x, y) information
    coord = collections.namedtuple('coord', ['x', 'y'])
    c = coord(x=x, y=y)
    return c


def getRoutePathTimeVehicle(veh, route="null"):
    """
    Calculates the total estimated time, considering the current road network conditions, of the route of a particular
    vehicle (for it's particular internal edge weights)

    Args:
        veh (str): The vehicle with the route to test
        route (str[]): The route the vehicle is taking
    Returns:
        int: The estimated route time for veh (for defined route, otherwise current)
    """
    currentTime = sumo.Main.getCurrentTime()
    totalEstimatedTime = 0
    # If route has not been defined, set route to the current vehicle route
    if route == "null":
        route = traci.vehicle.getRoute(veh)

    for edge in route:
        # This is the vehicle's internal travel time for this edge
        vehAdaptedTime = traci.vehicle.getAdaptedTraveltime(veh, time=currentTime, edgeID=edge)
        # If adapted travel time has not been set
        if vehAdaptedTime == -1001.0:
            # Setting the vehicle's internal edge travel time to be the same as the global edge travel time
            vehAdaptedTime = func.edgeSpeedGlobal[edge]
        totalEstimatedTime += vehAdaptedTime
        # Sets the vehicle's internal travel time for that edge
        traci.vehicle.setAdaptedTraveltime(vehID=veh, edgeID=edge, time=vehAdaptedTime)

    return totalEstimatedTime


def getGlobalRoutePathTime(route, realTime=True):
    """
    Calculates the total path time on a global scale, not specific to a vehicle

    Args:
        route (str): The route across the road network
        realTime (bool): This specifies whether or not the true current travel times should be used or if the user wants
        to test based on a certain adjusted road network (the adjustedEdgeSpeedGlobal) for rerouting purposes
    Returns:
        int: The estimated route times
    """
    totalEstimatedTime = 0

    if realTime:
        for edgeRealtime in route:
            try:
                totalEstimatedTime += func.edgeSpeedGlobal[edgeRealtime]
            except Exception:
                pass
    else:
        for edge in route:
            totalEstimatedTime += func.adjustedEdgeSpeedGlobal[edge]

    return totalEstimatedTime


def getGlobalEdgeWeights():
    """
    Populates the global edge weight variable, which stores the edge and corresponding estimated travel time
    """
    # Clears the mapping for this timestep
    # edgeSpeedGlobal.clear()
    for edge in traci.edge.getIDList():
        travelTime = traci.edge.getTraveltime(edge)
        """
        Sometimes congestion skews the road traffic conditions (this is down to the SUMO simulator itself, not my work).
        For example, if there is congestion ahead and the road is at a standstill for some reason (could be down to, 
        for example a traffic light) SUMO views this as virtually infinite expected travel time and will therefore
        have a huge negative impact on the travel times for the road network. So, I decided to bound edges to 15x 
        their free-flow travel speed conditions in an attempt to alleviate this.
        """
        if travelTime > (initialFunc.freeFlowSpeed[edge] * FREE_FLOW_TRAVEL_TIME_MAXIMUM):
            travelTime = initialFunc.freeFlowSpeed[edge] * FREE_FLOW_TRAVEL_TIME_MAXIMUM

        func.edgeSpeedGlobal[edge] = travelTime
        func.adjustedEdgeSpeedGlobal[edge] = travelTime



        # Initially setting the weights for the road network as being the current estimated travel times
        traci.edge.adaptTraveltime(edge, travelTime)


def fairnessIndex():
    """
    This is the fairness index, F, of all of the vehicle's QOE's in the network currently. This hopes to determine the
    fairness of the system as a whole

    Returns:
        fairness (float): This is the fairness index, F
        standardDeviation (float): This is the standard deviation of the QOEs
    """
    global vehiclesInNetwork

    # For all vehicles currently in the network work out the fairness index
    vehiclesList = vehiclesInNetwork

    if not vehiclesList:
        vehiclesList = traci.vehicle.getIDList()

    # All QOE values and highest and lowest values observed
    _, qoe, highestQOE, lowestQOE = selectVehiclesBasedOnFairness(vehiclesList)

    qoeValues = list(qoe.values())

    standardDeviation = np.nanstd(np.where(np.isclose(qoeValues, 0), np.nan, qoeValues))

    fairness = 1 - ((2 * standardDeviation) / (highestQOE - lowestQOE))

    print(standardDeviation)
    print(fairness)

    return fairness, standardDeviation


def updateVehicleTotalEstimatedTimeSpentInSystem(period=0):
    """
    This updates the total time spent in the system for each vehicle. Initially, a rough estimate of the time spent
    is calculated by incrementing the total time by the rerouting period IF they were present and WEREN'T stopped during
    the period between the previous and current rerouting period.

    Afterwards, a check is made for vehicles which have
    exited the simulation, once they have exited the simulation an accurate time is inserted???????????

    Args:
        period (int): This is the time period in which this method is repeated
    """

    """ Incrementing all of the vehicle's current time spent in the simulation """
    if period == 0:
        period = func.REROUTING_PERIOD
    # All vehicles in the road network
    for vehicle in traci.vehicle.getIDList():

        # Current status of the vehicle, if stopped (not defined as waiting at a traffic light), then True
        currentStatus = traci.vehicle.isStopped(vehicle)
        # If vehicle didn't exist in the system for the last rerouting period
        if vehicle not in stoppedStateLastPeriod:
            stoppedStateLastPeriod[vehicle] = currentStatus
        # If the vehicle has been stopped for both periods (assumption that they haven't moved between the
        # periods) then we will not increment the time spent in the simulation for that vehicle (although
        # the vehicle has been present in the system it is not actually using the system as it's stopped and
        # therefore shouldn't be penalised because of it)
        if not (stoppedStateLastPeriod[vehicle] and currentStatus):
            timeSpentInNetwork[vehicle] += period
        else:
            timeSpentStopped[vehicle] += period
            # REMOVE THIS IS FOR TESTING ONLY
            print("Vehicle WAS in stopped state")

        stoppedStateLastPeriod[vehicle] = currentStatus

def vehiclesDepartedAndArrived(i):
    """
    This tracks the vehicles which have just departed in the simulation and the vehicles which have left the simulation
    once they have arrived at their destination

    Args:
        i (int): The timestep of the simulation
    """

    """ Checking for vehicle's which have just entered the system """
    for vehicle in traci.simulation.getDepartedIDList():
        departureTime[vehicle] = i
        # If vehicle has never appeared in the system (also not stored on database) then initialise all of the values
        if vehicle not in timeSpentInNetwork:
            timeSpentInNetwork[vehicle] = 0
        if vehicle not in func.vehicleReroutedAmount:
            func.vehicleReroutedAmount[vehicle] = 0
        if vehicle not in func.cumulativeExtraTime:
            func.cumulativeExtraTime[vehicle] = 0
        # This is reset every time the simulation is restarted and doesn't need to be tracked between simulations
        timeSpentStopped[vehicle] = 0

    """ Checking for vehicle's which have finished their trip in the system """
    # Checking which vehicles have left the system during this timestep
    for vehicle in traci.simulation.getArrivedIDList():
        arrivalTime[vehicle] = i
        # With time spent with the vehicle in a stopped state being taken into account.
        additionalTimeRunning = (arrivalTime[vehicle] - departureTime[vehicle]) - timeSpentStopped[vehicle]
        # If the vehicle has made a previous appearance in the system
        if vehicle in initialTimeSpentInNetwork:
            # If less than 0 then make 0
            if additionalTimeRunning < 0:
                timeSpentInNetwork[vehicle] = 0
            else:
                # Update timeSpentInNetwork away from approximate to accurate time
                timeSpentInNetwork[vehicle] = initialTimeSpentInNetwork[vehicle] + additionalTimeRunning
        else:
            # If less than 0 then make 0
            if additionalTimeRunning < 0:
                timeSpentInNetwork[vehicle] = 0
            else:
                # First time
                timeSpentInNetwork[vehicle] = additionalTimeRunning

def selectVehiclesBasedOnFairness(reroutedList):
    """
    Selects vehicles for rerouting based on their current rerouting metrics

    Args:
        reroutedList (set()): All of the vehicles which are eligible to be rerouted

    Returns:
        reroutedFairly (set()): The vehicles which shall be rerouted due to their fairness measures
    """
    # Holds all of the vehicles which will be rerouted when fairness is taken into consideration
    reroutedFairly = []

    # Quality of Experience relates to the fairness in which the vehicle has experienced throughout their simulations,
    # the higher the QOE the more the system has been 'fair' to the user; similarly, lower values indicate an unfairness
    # given by the system to the vehicle
    qoe = {}

    # This is the largest value for cumulativeExtraTime out of all of the vehicles
    largestCET = 0
    # The largest vehicleReroutedAmount for all of the vehicles in reroutedList
    largestVRA = 0
    # This is the least amount of time spent in the system
    leastTime = sys.maxsize
    # This is the most time spent in the system
    mostTime = 0

    # Finding largest values for CET and VRA
    for vehicle in reroutedList:
        vehicleVRA = func.vehicleReroutedAmount[vehicle]
        vehicleCET = func.cumulativeExtraTime[vehicle]
        vehicleTimeSpent = timeSpentInNetwork[vehicle]

        if vehicleVRA > largestVRA:
            largestVRA = vehicleVRA
        if vehicleCET > largestCET:
            largestCET = vehicleCET
        if vehicleTimeSpent > mostTime:
            mostTime = vehicleTimeSpent
        if vehicleTimeSpent < leastTime:
            leastTime = vehicleTimeSpent

    # This is the largest QOE value (not necessarily the largest normalised QOE)
    largestQOEVal = 0
    # Largest normalised QOE
    largestQOE = 0
    # Smallest normalised QOE
    smallestQOE = sys.maxsize
    # This is the smallest qoe
    smallestQOEVal = sys.maxsize

    # Fairness is calculated using these 2 values
    for vehicle in reroutedList:
        vehicleVRA = func.vehicleReroutedAmount[vehicle]
        vehicleCET = func.cumulativeExtraTime[vehicle]
        vehicleTimeSpent = timeSpentInNetwork[vehicle]

        # Working out the fraction of the largest VRA and CET that the vehicle has
        if largestVRA == 0:
            vraPercentage = 0
        else:
            vraPercentage = vehicleVRA / largestVRA

        if largestCET == 0:
            cetPercentage = 0
        else:
            cetPercentage = vehicleCET / largestCET

        """
        This is used to normalise the QOE of each of the vehicles, keeping in mind that vehicles which has spent
        longer in the simulation will use the system more (therefore more reroutings). This means that vehicles which
        are new to the system will always be chosen for rerouting as the system views them as having experienced more
        fairness (this is not true of course, new vehicles who have experienced no rerouting should be considered in a 
        similar way to old vehicles [which have used the system for a long time] whom have not experienced many
        reroutings for their time using the system, therefore this is required to normalise the QOE values based on the
        time spent in the system.
        """
        if mostTime == 0:
            normalisedTime = 0
        else:
            normalisedTime = vehicleTimeSpent / mostTime

        # mainMeasures is the ratio of VRA and CET, with no concern for time
        mainMeasures = ((vraPercentage * func.FAIRNESS_WEIGHTING) + (cetPercentage * (1 - func.FAIRNESS_WEIGHTING)))

        if normalisedTime == 0:
            val = 0
        else:
            val = mainMeasures / normalisedTime

        # qoeVal represents the QOE in it's non-normalised form
        qoeVal = val
        qoe[vehicle] = qoeVal
        if qoeVal > largestQOEVal:
            largestQOEVal = qoeVal
        if qoeVal < smallestQOEVal:
            smallestQOEVal = qoeVal

    """ Normalising the QOE values based on the amount of time spent in the system in total """

    for vehicle in qoe:
        notNormalised = qoe[vehicle]
        # The QOE value can be between 0 to largestQOEVal value, we multiply 10 so that the range is extended from 0-10
        if largestQOEVal == 0:
            qoe[vehicle] = 1
        else:
            # Division by 0 avoidance
            if largestQOEVal - smallestQOEVal == 0:
                # Set all values to 10 given that they all have the same QOE value
                qoe = dict.fromkeys(qoe, 10)
                break
            else:
                # Normalising QOE values back to range 0-1 and then multiplying by 10 to get within range 0-10.
                # Additionally, we negate this from 10 (qoeVal is +10 more than the QOE we need)
                qoe[vehicle] = 10 - ((notNormalised - smallestQOEVal) / (largestQOEVal - smallestQOEVal) * 10)
        if largestQOE < qoe[vehicle]:
            largestQOE = qoe[vehicle]
        if smallestQOE > qoe[vehicle]:
            smallestQOE = qoe[vehicle]

    """ Selecting top PERCENTILE to reroute (top PERCENTILE of fairness) """

    # Checking if all QOE values for all vehicles are the same (and if so, reroute them all)
    if len(set(qoe.values())) == 1:
        reroutedFairly = list(qoe.keys())
    else:
        """" Select vehicles based on their respective QOEs"""
        # This is the cut-off point in which vehicles having a higher QOE shall be selected for rerouting
        qoePercentile = largestQOE * func.PERCENTILE

        # List containing the vehicles with qoe's >= qoePercentile (those which shall be rerouted)
        reroutedFairly = [k for k, v in qoe.items() if v >= qoePercentile]

    largestQOE = largestQOE / 10
    smallestQOE = smallestQOE / 10

    return reroutedFairly, qoe, largestQOE, smallestQOE