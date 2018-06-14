import random
import time

import sys
import traci

from src.project.code import InitialMapHelperFunctions as initialFunc
from src.project.code import SimulationFunctions as sim
from src.project.code import SumoConnection as sumo
from src.project.code.SimulationFunctions import selectVehiclesBasedOnFairness

__author__ = "Jonathan Harper"

"""
The RoutingFunctions.py file deals with functions which are called during the runtime of the simulation in order to 
manipulate the vehicles within the simulation.

Can be thought of as 'setters' during the simulation runtime
"""

# This is the penalisation factor given to the edge estimated travel time
PENALISATION = 2
# This ensures that the route chosen in kPaths() doesn't exceed the bestPath * KPATH_MAX_ALLOWED_TIME
KPATH_MAX_ALLOWED_TIME = 1.2
# The maximum amount of retries for kPaths until it's decided to take the current routes in the possible route list
KPATH_TIMEOUT = 15
# This is the percentage of vehicles in the top percentile range which will be considered for rerouting based on their
# fairness (vehicle chosen if their QOE >= PERCENTILE * max QOE of vehicle's considered)
PERCENTILE = 0.6

# The period in timesteps in which rerouting occurs during the simulation
REROUTING_PERIOD = 100

# Stores the edge and their CURRENT corresponding estimated travel time
edgeSpeedGlobal = {}
# Stores the edge and their ADJUSTED corresponding estimated travel time (allows for penalisation of travel times)
adjustedEdgeSpeedGlobal = {}

# This is the number of times a vehicle has been rerouted in the form {vehicleID: vehicleReroutedAmount)
vehicleReroutedAmount = {}
# This is the cumulative extra (estimated) time in which the vehicle has experienced due to the rerouting. Represented
# in the form {vehicleID: cumulativeExtraTimeSpent (s)}
cumulativeExtraTime = {}
# This is the weighting of the factors which determine fairness. Fairness is determined by the ratio between
# vehicleReroutedAmount:cumulativeExtraTime, a value of 0.6 means a weighting of 60:40
FAIRNESS_WEIGHTING = 0.6

# This stores the vehicles rerouted during the 'rerouting period' in which the vehicles are rerouted
reroutedVehicles = set()


# def initialiseRerouteVehicles(edgeID):
#     """
#     Initialisation options used for all rerouting purposes (both edge and lane)
#
#     Args:
#         edgeID (str): The edge in which the congestion has occurred
#
#     Returns:
#         vehiclesList (str[]): The list of vehicle ID's which appear on the edges up to K_MAX from the congested edge
#         edgesList ({str: str[]}): The edges and their corresponding vehicles in the order {edge : vehicle (str[])}
#         reroutedList (set()): The set of all of the vehicles to be rerouted
#         vehicleEdge ({str: str}): the vehicle ID with the corresponding edge ID
#     """
#
#     # The list of vehicles existing on the edges
#     vehiclesList = []
#     # The edges and their corresponding vehicles in the order {edge : vehicle (str[])}
#     edgesList = {}
#     # This is the list of all of the vehicles which have been rerouted
#     reroutedList = []
#     # vehicle: edge (that the vehicle is on)
#     vehicleEdge = {}
#
#     # Going through the incoming edges and identifying vehicles on them
#     for edge in initialFunc.multiIncomingEdges[edgeID]:
#         vehiclesOnEdge = traci.edge.getLastStepVehicleIDs(edge)
#         # Appending the list of vehicles from edge onto vehiclesList
#         vehiclesList.extend(vehiclesOnEdge)
#
#         for vehicle in vehiclesOnEdge:
#             vehicleEdge[vehicle] = edge
#
#         # If vehicles exist on that edge
#         if vehiclesOnEdge:
#             edgesList[edge] = vehiclesOnEdge
#
#     # Removing vehicles from the list of vehicles for consideration of rerouting if they have already been rerouted
#     # in this rerouting period
#     for vehicle in vehiclesList:
#         if vehicle in reroutedVehicles:
#             vehiclesList.remove(vehicle)
#
#     return vehiclesList, edgesList, reroutedList, vehicleEdge


# def rerouteSelectedVehiclesEdge(edgeID, kPathsBool=False, fairness=False):
#     """
#     Selects the vehicles to be rerouted from edgeID (the edge which is currently congested) and reroutes them based
#     on current estimated travel times
#
#     Args:
#         edgeID (str): The edge in which the congestion is occurring
#         kPathsBool (bool): True if kPaths is being performed
#         fairness (bool): True if fairness should be considered for the vehicles
#
#     Returns:
#         str[]: The list of vehicles which have been rerouted
#     """
#     vehiclesList, edgesList, reroutedList, vehicleEdge = initialiseRerouteVehicles(edgeID)
#
#     # What vehicles have the edgeID
#     for vehicle in vehiclesList:
#         # The old/current path of the vehicle
#         oldPath = traci.vehicle.getRoute(vehicle)
#         # If the edgeID exists in the vehicles current route then reroute them
#         if edgeID in oldPath:
#             if kPathsBool:
#                 kPaths(vehicle, vehicleEdge[vehicle])
#             else:
#                 # Reroute vehicles based on current travel times
#                 traci.vehicle.rerouteTraveltime(vehicle, currentTravelTimes=True)
#             # reroutedList.add(vehicle)
#             reroutedList.append(vehicle)
#             newPath = traci.vehicle.getRoute(vehicle)
#             # If the route has been changed
#             if oldPath != newPath:
#                 # Incrementing vehicle reroute number
#                 vehicleReroutedAmount[vehicle] += 1
#                 # if vehicle in vehicleReroutedAmount:
#                 #     vehicleReroutedAmount[vehicle] += 1
#                 # else:
#                 #     vehicleReroutedAmount[vehicle] = 1
#
#     if fairness:
#         sim.reroutedList = selectVehiclesBasedOnFairness(reroutedList)
#
#     reroutedVehicles.update(reroutedList)
#
#     return reroutedList

# def rerouteVehicles(roadSegmentID, lane, type='', kPathsBool=False, fairness=False):
#
#     # # Ensures that a type has been entered and that it conforms to either 'edge', 'lane', or the shorthand variants
#     # # 'e' and 'l' respectively
#     # if type != 'edge' or type != 'e' or type != 'lane' or type != 'l':
#     #     raise ValueError('Please insert a correct value for the parameter \'type\' - refers to the type of road '
#     #                      'segment, either \'edge\' or \'lane\', alternatively shorthand \'e\' and \'l\' can be used '
#     #                      'respectively.', type)
#
#     # If the specified roadSegmentID is a lane
#     if lane:
#         # The edge in which the lane belongs
#         edgeID = initialFunc.lanesNetwork[roadSegmentID]

def selectVehiclesForRerouting(roadSegmentID, fairness=False):
    """
    This selects the vehicles which are eligible to be rerouted, eligibility in determined by a number of factors.
    Natively, eligibility is determined if the vehicle's route shall stray into the congested area, if so rerouting
    should be considered.

    Fairness is also taken into account, (if selected) vehicle's are chosen based on how fairly they've been treated in
    the system compared to other vehicle's which could run into the congested area.

    Args:
        roadSegmentID (str): The ID of a segment of road, either an entire edge or an individual lane
        fairness (bool): True if fairness should be considered for the vehicles

    Returns:
        reroutingConsiderationList (set()): This is the list of all of the vehicles to be considered for rerouting
        vehicleEdge ({str: str}): the vehicle ID with the corresponding edge ID
        vehicleOldRoute ({str: str[]}): The vehicle and it's corresponding route (before rerouting)
    """

    # True if the road segment is a lane
    laneBool = False

    # Automatically work out if the road segment ID belongs to a lane or an edge
    if roadSegmentID in initialFunc.lanesNetwork:
        laneBool = True
        # The edge in which the lane belongs
        edgeID = initialFunc.lanesNetwork[roadSegmentID]
        """ Effectively, we are testing if the vehicles need to occupy this specific lane to continue their journey, or if
        another lane on the edge could instead be used/is necessary """
        outgoingLanes = initialFunc.directedGraphLanes[roadSegmentID]
    elif roadSegmentID not in initialFunc.edgesNetwork:
        # The road segment ID doesn't exist as either an edge or a lane
        initialFunc.endSimWithError("Road segment ID \'{}\' doesn't exist in the road network.".format(roadSegmentID))
    else:
        # The road segment is an edge, so set the local variable
        edgeID = roadSegmentID

    # The list of vehicles existing on the edges
    vehiclesList = []
    # The edges and their corresponding vehicles in the order {edge : vehicle (str[])}
    edgesList = {}
    # This is the list of all of the vehicles to be considered for rerouting
    reroutingConsiderationList = []
    # vehicle: edge (that the vehicle is on)
    vehicleEdge = {}
    # vehicle: oldRoute
    vehicleOldRoute = {}

    # Going through the incoming edges and identifying vehicles on them
    for edge in initialFunc.multiIncomingEdges[edgeID]:
        vehiclesOnEdge = traci.edge.getLastStepVehicleIDs(edge)
        # Appending the list of vehicles from edge onto vehiclesList
        vehiclesList.extend(vehiclesOnEdge)

        for vehicle in vehiclesOnEdge:
            vehicleEdge[vehicle] = edge

        # If vehicles exist on that edge
        if vehiclesOnEdge:
            edgesList[edge] = vehiclesOnEdge

    # Removing vehicles from the list of vehicles for consideration of rerouting if they have already been rerouted
    # in this rerouting period
    for vehicle in vehiclesList:
        if vehicle in reroutedVehicles:
            vehiclesList.remove(vehicle)
        # Removing any vehicle which is currently in the 'stopped' state (this is not the same as 'waiting', e.g.
        # waiting at a traffic light)
        if traci.vehicle.isStopped(vehicle):
            vehiclesList.remove(vehicle)

    """ Only selecting those vehicles which actually pass through the congested road segment (treated differently 
    depending on if the congestion is only affecting the lane or the entire edge) """
    for vehicle in vehiclesList:
        oldRoute = traci.vehicle.getRoute(vehicle)
        vehicleOldRoute[vehicle] = oldRoute
        # If the edgeID exists in the vehicles current route
        if edgeID in oldRoute:
            if laneBool:
                # Finding the next edge and corresponding lane of the vehicle to see if it's current route shall be
                # affected by the congestion existent on the lane
                congestionIndex = oldRoute.index(edgeID)
                nextEdge = oldRoute[congestionIndex + 1]
                lanesInNextEdge = initialFunc.edgesNetwork[nextEdge]

                """ Testing if lanes present in the edge after the congested edge (of the vehicle's route) are any of 
                the outgoing lanes from the congested lane, otherwise do not reroute the vehicle as this congestion will
                 not affect the vehicle """
                if any(lane in lanesInNextEdge for lane in outgoingLanes):
                    reroutingConsiderationList.append(vehicle)
            else:
                # Vehicle must be affected by congestion as congestion is throughout the entire edge
                reroutingConsiderationList.append(vehicle)

    if fairness:
        reroutingConsiderationList, _, _, _ = sim.selectVehiclesBasedOnFairness(reroutingConsiderationList)

    return reroutingConsiderationList, vehicleEdge, vehicleOldRoute, []

def rerouteSelectedVehicles(roadSegmentID, kPathsBool = False, fairness = False):
    """
    Selects the vehicles to be rerouted from roadSegmentID (the edge OR lane which is currently congested) and reroutes
    them based on current estimated travel times

    Args:
        roadSegmentID (str): The ID of a segment of road, either an entire edge or an individual lane
        kPathsBool (bool): True if kPaths is being performed
        fairness (bool): True if fairness should be considered for the vehicles

    Returns:
        str[]: The list of vehicles which have been rerouted
    """

    vehiclesToReroute, vehicleEdge, vehicleOldRoute, bestRouteVehicles = selectVehiclesForRerouting(roadSegmentID,
                                                                                                    fairness)

    # Set of vehicles in which rerouting has actually occurred (after rerouting has been ran the route has changed from
    # the old route held in vehicleOldRoute).
    vehiclesUndergoneRerouting = set()

    for vehicle in vehiclesToReroute:
        # Rerouting either through kPaths or through DSP
        if kPathsBool:
            kPaths(vehicle, vehicleEdge[vehicle])
        else:
            # Reroute vehicles based on current travel times
            traci.vehicle.rerouteTraveltime(vehicle, currentTravelTimes=True)

        newPath = traci.vehicle.getRoute(vehicle)
        # If the route has been changed
        if vehicleOldRoute[vehicle] != newPath:
            vehiclesUndergoneRerouting.add(vehicle)
            # Vehicle shouldn't be rerouted again in the same rerouting period
            reroutedVehicles.add(vehicle)
            # Incrementing vehicle reroute number
            vehicleReroutedAmount[vehicle] += 1
            # if vehicle in vehicleReroutedAmount:
            #     vehicleReroutedAmount[vehicle] += 1
            # else:
            #     vehicleReroutedAmount[vehicle] = 1

    return vehiclesUndergoneRerouting

# def rerouteSelectedVehiclesLane(laneID, kPathsBool=False):
#     """
#     Selects the vehicles to be rerouted from the laneID (the lane which is currently congested) which belongs to edgeID
#     and reroutes them based on current estimated travel times
#
#     Args:
#         laneID (str): The lane in which the congestion is occurring
#         kPathsBool (bool): True if kPaths needs to be performed for each vehicle
#         fairness (bool): True if fairness should be considered for the vehicles
#
#     Returns:
#         str[]: The list of vehicles which have been rerouted
#     """
#     # The edge in which the lane belongs
#     edgeID = initialFunc.lanesNetwork[laneID]
#
#     totalTime = 0
#     startTime = time.clock()
#
#     vehiclesList, edgesList, reroutedList, vehicleEdge = initialiseRerouteVehicles(edgeID)
#
#     # Effectively, we are testing if the vehicles need to occupy this specific lane to continue their journey, or if
#     # another lane on the edge could instead be used/is necessary
#     outgoingLanes = initialFunc.directedGraphLanes[laneID]
#
#     # What vehicles have the edgeID
#     for vehicle in vehiclesList:
#         # The old/current path of the vehicle
#         oldPath = traci.vehicle.getRoute(vehicle)
#         # If the edgeID exists in the vehicles current route then reroute them
#         if edgeID in oldPath:
#             congestionIndex = oldPath.index(edgeID)
#             # The edge intended to be taken by the vehicle directly after they have left the congested edge
#             nextEdge = oldPath[congestionIndex + 1]
#             lanesInNextEdge = initialFunc.edgesNetwork[nextEdge]
#
#             # Testing if lanes present in the edge after the congested edge (of the vehicle's route) are any of the
#             # outgoing lanes from the congested lane, otherwise do not reroute the vehicle as this congestion will not
#             # affect the vehicle.
#             if any(lane in lanesInNextEdge for lane in outgoingLanes):
#                 # Incrementing vehicle reroute number
#                 vehicleReroutedAmount[vehicle] += 1
#
#                 if kPathsBool:
#                     kPaths(vehicle, vehicleEdge[vehicle])
#                 else:
#                     # Reroute vehicle
#                     traci.vehicle.rerouteTraveltime(vehicle, currentTravelTimes=False)
#                 # reroutedList.add(vehicle)
#                 reroutedList.append(vehicle)
#
#     if fairness:
#         reroutedList = sim.selectVehiclesBasedOnFairness(reroutedList)
#
#     reroutedVehicles.update(reroutedList)
#
#     return reroutedList


# def getRoutePathTime(route):
#     """
#     Calculates the total estimated time, considering the current road network conditions (for the entire road network)
#     of the route passed
#
#     Args:
#         route (str[]): The route in which the edges shall be checked for
#     Returns:
#         int: The estimated route time to take the route
#     """
#     totalEstimatedTime = 0
#
#     for edge in route:
#         # This is the vehicle's internal travel time for this edge
#         vehAdaptedTime = traci.vehicle.getAdaptedTraveltime(veh, time=currentTime, edgeID=edge)
#         # If adapted travel time has not been set
#         if vehAdaptedTime == -1001.0:
#             # Setting the vehicle's internal edge travel time to be the same as the global edge travel time
#             vehAdaptedTime = edgeSpeedGlobal[edge]
#         totalEstimatedTime += vehAdaptedTime
#         # Sets the vehicle's internal travel time for that edge
#         traci.vehicle.setAdaptedTraveltime(vehID=veh, edgeID=edge, time=vehAdaptedTime)
#
#     return totalEstimatedTime


# def kPaths(veh):
#     """
#     Determines k shortest paths for the vehicle and randomly assigns one
#
#     Args:
#         veh (str): The vehicle which needs rerouting
#     Returns:
#         routeList ([[str]]): The list of routes in which the vehicle could possibly be chosen to take (in the form
#         [[route1], [route2]... [routeK_MAX]])
#     """
#
#     # Contains a list of the routes (where each route consists of a list of edges)
#     routeList = []
#     # Counter
#     k = 1
#     # A set of all of the edges
#     edgesSet = set()
#
#     # Finding the best possible route for the vehicle
#     traci.vehicle.rerouteTraveltime(veh)
#     # The vehicle's current route
#     currentRoute = traci.vehicle.getRoute(veh)
#     bestTime = getGlobalRoutePathTime(currentRoute)
#
#     # Populating lists with the best route
#     routeList.append(currentRoute)
#     edgesSet.update(currentRoute)
#
#     # Creating up to k-1 additional routes
#     while k < sumo.K_MAX:
#         print()
#         print("This is the current route time {}".format(getRoutePathTimeVehicle(veh, currentRoute)))
#         print("This is the global route times {}".format(getGlobalRoutePathTime(currentRoute)))
#         penalisePathTime(currentRoute)
#
#         traci.vehicle.rerouteTraveltime(veh, currentTravelTimes=True)
#         newRoute = traci.vehicle.getRoute(veh)
#         newRouteTime = getGlobalRoutePathTime(newRoute, False)
#
#         currentRoute = newRoute
#         # Ensuring the route doesn't exist within the routeList
#         if currentRoute not in routeList:
#             # New route's estimated time doesn't exceed >20% of the optimal route time
#             if newRouteTime <= bestTime*1.2:
#                 routeList.append(currentRoute)
#                 edgesSet.update(currentRoute)
#                 k += 1
#             else:
#                 break
#
#     randomNum = random.randint(0, sumo.K_MAX - 1)
#     # Selecting a random route
#     routeSelection = routeList[randomNum]
#
#     traci.vehicle.setRoute(vehID=veh, edgeList=routeSelection)
#
#     # Setting the adjusted travel times for the edges to their default (the original estimated travel time given the
#     # current network traffic conditions).
#     adjustedEdgeSpeedGlobal = deepcopy(edgeSpeedGlobal)
#     for edge in adjustedEdgeSpeedGlobal.keys():
#         traci.edge.adaptTraveltime(edgeID=edge, time=adjustedEdgeSpeedGlobal[edge])
#
#     return routeList

def kPaths(veh, currentEdge):
    """
    Determines k shortest paths for the vehicle and randomly assigns one

    Args:
        veh (str): The vehicle which needs rerouting
        currentEdge (str): The edge in which the vehicle is currently situated
    Returns:
        routeList ([[str]]): The list of routes in which the vehicle could possibly be chosen to take (in the form
        [[route1], [route2]... [routeK_MAX]])
    """
    # Contains a list of the routes (where each route consists of a list of edges)
    routeList = []
    # These are the routes adjusted for the beginning edge being the edge in which the vehicle is currently present
    #
    # Counter
    k = 1
    # A set of all of the edges
    edgesSet = set()

    # Finding the best possible route for the vehicle
    traci.vehicle.rerouteTraveltime(veh, currentTravelTimes=False)
    traci.vehicle.rerouteTraveltime(veh, currentTravelTimes=False)

    # The vehicle's current route
    currentRoute = traci.vehicle.getRoute(veh)
    # Element of the current edge within the currentRoute
    currentEdgeIndex = currentRoute.index(currentEdge)
    # Altered route with the first element of the route being the current edge
    alteredRoute = currentRoute[currentEdgeIndex:]

    bestTime = sim.getGlobalRoutePathTime(alteredRoute)
    adjustedEdge ={}

    bestRoute = alteredRoute

    for edge in alteredRoute:
        adjustedEdge[edge] = edgeSpeedGlobal[edge]

    # Populating lists with the best route
    routeList.append(alteredRoute)
    edgesSet.update(alteredRoute)

    currentRoute = alteredRoute

    # This is a fail safe in case there are less paths than K_MAX available for the vehicle to take
    timeOut = 0

    # Creating up to k-1 additional routes
    while k < sumo.K_MAX:
        penalisePathTimeVehicle(veh, currentRoute, adjustedEdge)

        traci.vehicle.rerouteTraveltime(veh, currentTravelTimes=False)
        newRoute = traci.vehicle.getRoute(veh)
        newRouteTime = sim.getGlobalRoutePathTime(newRoute)
        newRouteVehTime = adjustedEdge
        # Only taking the selection in which the vehicle can take (with the route beginning on the currently occupied
        # edge)
        currentRoute = newRoute[currentEdgeIndex:]
        newRouteTime2 = sim.getGlobalRoutePathTime(currentRoute)
        newRouteTime3 = sim.getGlobalRoutePathTime(newRoute[currentEdgeIndex:])
        # Ensuring the route doesn't exist within the routeList and that the route contains the edge in which the
        # vehicle is currently occupying
        if currentRoute not in routeList and currentEdge in currentRoute and currentRoute != bestRoute:
            timeOut = 0
            # New route's estimated time doesn't exceed >KPATH_MAX_ALLOWED_TIME of the optimal route time
            if newRouteTime <= bestTime*KPATH_MAX_ALLOWED_TIME:
                for edge in currentRoute:
                    if edge not in adjustedEdge:
                        adjustedEdge[edge] = edgeSpeedGlobal[edge]
                routeList.append(currentRoute)
                edgesSet.update(currentRoute)
                k += 1
            else:
                break
        else:
            timeOut += 1
            # Time out limit exceeded
            if timeOut == KPATH_TIMEOUT:
                break

    randomNum = random.randint(0, k - 1)
    # Selecting a random route
    routeSelection = routeList[randomNum]

    # actualLocation = traci.vehicle.getLaneID(veh)
    # actual = initialFunc.lanesNetwork[actualLocation]

    # This is the time in which the route is estimated to take
    routeTime = sim.getGlobalRoutePathTime(routeSelection)
    # The amount of time extra in which the vehicle will travel in relation to it's optimal time
    extraTime = routeTime - bestTime

    # In case error with global path time occurs (SUMO issue with congestion)
    extraTime = congestionOccurrence(k, routeList, bestTime, extraTime)

        # shortestTime = sys.maxsize
        # shortestRoute = []
        # for route in routeSelection:
        #     time = sim.getGlobalRoutePathTime(routeSelection)
        #     if time < shortestTime:
        #         shortestRoute = route
        #
        # extraTime = 0
        # routeSelection = shortestRoute

    # Setting the additional (estimated) extra time in which the vehicle has taken due to reroutings
    cumulativeExtraTime[veh] += extraTime

    traci.vehicle.setRoute(veh, routeSelection)

    # Settings the vehicle's internal edge travel time back to the global edge travel time (resetting back to global)
    for edge in edgesSet:
        traci.vehicle.setAdaptedTraveltime(vehID=veh, edgeID=edge, time=edgeSpeedGlobal[edge])

    return routeList


# def k3Paths(veh):
#     """
#     Generates k-shortest paths for the vehicle and randomly selects one
#
#     Args:
#         veh (str): The vehicle which needs rerouting
#     """
#     # Getting the edge weights of the entire scenario for the current time step
#     getGlobalEdgeWeights()
#
#     # Set of all of the edges in which the vehicle's routes consist
#     edgesSet = set()
#     # A list containing the routes the vehicle can take
#     routeList = []
#     # Counter
#     k = 1
#
#     # Finding the best possible route for the vehicle
#     traci.vehicle.rerouteTraveltime(veh)
#     currentRoute = traci.vehicle.getRoute(veh)
#     # The best possible routes time taken
#     bestTime = getGlobalRoutePathTime(currentRoute)
#
#     # Populating lists with the best route
#     routeList.append(currentRoute)
#     edgesSet.update(currentRoute)
#
#     # Creating up to k-1 additional routes
#     while k < sumo.K_MAX:
#         # Penalising the currentRoute
#         penalisePathTimeVehicle(veh, currentRoute)
#
#         # Generating new route
#         traci.vehicle.rerouteTraveltime(veh, currentTravelTimes=True)
#         currentRoute = traci.vehicle.getRoute(veh)
#         newRouteTime = getGlobalRoutePathTime(currentRoute)
#
#         # Ensuring the route doesn't exist within the routeList
#         if currentRoute not in routeList:
#             # New route's estimated time doesn't exceed >20% of the optimal route time
#             if newRouteTime <= bestTime*1.2:
#                 routeList.append(currentRoute)
#                 edgesSet.update(currentRoute)
#                 k += 1
#             else:
#                 break
#
#     # Selecting a random route
#     randomNum = random.randint(0, sumo.K_MAX - 1)
#     routeSelection = routeList[randomNum]
#     traci.vehicle.setRoute(vehID=veh, edgeList=routeSelection)
#
#     # Settings the vehicle's internal edge travel time back to the global edge travel time
#     for edge in edgesSet:
#         traci.vehicle.setAdaptedTraveltime(vehID=veh, edgeID=edge, time=edgeSpeedGlobal[edge])

def congestionOccurrence(k, routeList, bestTime, extraTime):
    """
    For some reason, the best time (the route which SUMO considers the best) will not be the best time due to
    skewed congestion detection techniques (the expected time returned by SUMO may be huge to congestion which
    SUMO is unable to accurately predict). Therefore, if this happens (very rarely happens), another route is chosen
    until extraTime is >= 0

    Args:
        k (int): The number of routes in the list
        routeList (str[]): The possible k routes
        bestTime (float): The best time in which the vehicle can achieve
    """
    extraTimeTimeOut = 0

    while extraTime < 0:
        randomNum = random.randint(0, k - 1)
        routeSelection = routeList[randomNum]
        routeTime = sim.getGlobalRoutePathTime(routeSelection)
        extraTime = routeTime - bestTime

        extraTimeTimeOut += 1

        if extraTimeTimeOut == 3:
            travelTime = 0

            # Essentially attempts to remove the problem edges from the travel time
            for edge in routeSelection:
                # Selects the edges with edge weights > free flow speed travel times * FREE_FLOW_TRAVEL_TIME_MAXIMUM as
                # these edges have suffered an issue
                if edgeSpeedGlobal[edge] > initialFunc.freeFlowSpeed[edge] * sim.FREE_FLOW_TRAVEL_TIME_MAXIMUM:
                    travelTime += initialFunc.freeFlowSpeed[edge] * 2
                else:
                    travelTime += edgeSpeedGlobal[edge]

            extraTime = travelTime
            break

    return extraTime

def penalisePathTimeVehicle(veh, route, adjustedEdge={}):
    """
    Penalises the path time of a particular vehicle, used for k-shortest paths

    Args:
        veh (str): The vehicle which needs to have the adjusted route time
        route (str): The route to be penalised for the vehicle, veh
    """
    currentSysTime = sumo.Main.getCurrentTime()
    for edge in route:
        currentAdaptedTime2 = adjustedEdge[edge]
        # Sets an adapted travel time for an edge (specifically for that vehicle)
        currentAdaptedTime = traci.vehicle.getAdaptedTraveltime(vehID=veh, edgeID=edge, time=currentSysTime)
        adjustedEdge[edge] = currentAdaptedTime2 * PENALISATION
        # Penalise the travel time by a multiplication of PENALISATION
        traci.vehicle.setAdaptedTraveltime(vehID=veh, edgeID=edge, time=adjustedEdge[edge])




def penalisePathTime(route):
    """
    Penalises the path time of the edge

    Args:
        route (str): The edges (contained within the route) to be penalised
    """
    for edge in route:
        # Getting the current adapted time for that edge
        currentAdaptedTime = adjustedEdgeSpeedGlobal[edge]
        # Penalise the travel time by PENALISATION
        adjustedEdgeSpeedGlobal[edge] = currentAdaptedTime * 2
        traci.edge.adaptTraveltime(edge, adjustedEdgeSpeedGlobal[edge])


