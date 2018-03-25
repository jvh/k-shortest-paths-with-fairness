import traci

from src.project.small_manhattan.traci_code import SumoConnection as sumo


class Testing():

    def testVehicleSetEffort(self, vehicleID, edgeID):
        edgeEffortDouble = traci.edge.getEffort(edgeID, sumo.Main.getCurrentTime())
        traci.vehicle.setEffort(vehicleID, sumo.START_TIME, sumo.END_TIME, edgeID, edgeEffortDouble)

        print("Vehicle effort for {} on edge {} at time {}: {}".format(vehicleID, edgeID, sumo.Main.getCurrentTime(), traci.vehicle.getEffort(vehicleID, sumo.Main.getCurrentTime(), edgeID)))
        # print("Vehicle effort for " + vehicleID + " on edge " + edgeID + " at time " + sumo.Main.getCurrentTime())

    def test1Before(self):
        # Adding vehicle and associated route
        traci.route.add("startNode", ["46538375#5"])
        traci.vehicle.addFull("testVeh", "startNode", typeID="car")

        # GUI tracking vehicle and zoom
        traci.gui.trackVehicle("View #0", "testVeh")
        traci.gui.setZoom("View #0", traci.gui.getZoom() * sumo.ZOOM_FACTOR)

        # Changing the target of the vehicle to another edge
        traci.vehicle.changeTarget("testVeh", "569345537#2")

        traci.edge.setEffort("46538375#8", 1)
        traci.edge.setEffort("196116976#7", 2)

    def test1During(self, i):
        if(i == 10):
            self.testVehicleSetEffort("testVeh", "46538375#8");
            traci.vehicle.rerouteEffort("testVeh")

        traci.simulationStep()