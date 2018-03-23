package project.small_manhattan.code;

import de.tudresden.sumo.cmd.Vehicle;
import it.polito.appeal.traci.SumoTraciConnection;

import java.util.ArrayList;

public class DynamicShortestPath extends TestToRun {

    SumoTraciConnection conn;
    SimulationMain sim;

    public DynamicShortestPath() {
        conn = new SumoTraciConnection(SimulationMain.SUMO_BIN, SimulationMain.NORMAL_CONFIG);
//        sim.setConn(conn);
//        this.sim = sim;
    }

    protected void beforeLoop() {

    }

    void afterLoop() {

    }

    protected void duringLoop(int i) throws Exception {
//        System.out.println(sim.getCurrentTime());

        //Every 10 seconds
        if(i%100 ==0 ) {
            for(String vehID: (ArrayList<String>) conn.do_job_get(Vehicle.getIDList())) {
                System.out.println(vehID);
            }
        }
        conn.do_timestep();
    }

    protected SumoTraciConnection getConn() {
        return conn;
    }
}
