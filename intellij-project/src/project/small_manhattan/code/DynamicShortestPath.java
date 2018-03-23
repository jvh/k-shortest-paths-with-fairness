package project.small_manhattan.code;

import it.polito.appeal.traci.SumoTraciConnection;

public class DynamicShortestPath extends TestToRun {

    SumoTraciConnection conn;
    Simulation sim;

    public DynamicShortestPath(Simulation sim) {
        conn = new SumoTraciConnection(Simulation.SUMO_BIN, Simulation.NORMAL_CONFIG);
        this.sim = sim;
    }

    protected void beforeLoop() {

    }

    void afterLoop() {

    }

    protected void duringLoop(int i) {

    }

    protected SumoTraciConnection getConn() {
        return conn;
    }
}
