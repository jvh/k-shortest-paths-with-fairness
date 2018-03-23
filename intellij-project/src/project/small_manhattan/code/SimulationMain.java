package project.small_manhattan.code;

import de.tudresden.sumo.cmd.Simulation;
import it.polito.appeal.traci.SumoTraciConnection;

public class SimulationMain {

    public static final String NORMAL_CONFIG = "src/project/small_manhattan/configuration_files/normal/config.cfg";
    public static final String TEST_CONFIG = "src/project/small_manhattan/configuration_files/testing/config_test.cfg";

    //SimulationMain start and end times
    public static final int START_TIME = 0;
    public static final int END_TIME = 100000;
    //Zoom factor for GUI
    public static final int ZOOM_FACTOR = 12;

    public static final String SUMO_BIN = "D:/Program Files/SUMO/bin/sumo-gui.exe";

   //Is testing being done?
    public static final boolean TESTING = true;

    private static SumoTraciConnection conn;

    public SimulationMain(TestToRun ttr) {
        try {
            this.conn = ttr.getConn();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void main(String[] args) {
        Test test;
        DynamicShortestPath dsp;
        TestToRun ttr;

        if(TESTING) {
            test = new Test();
            ttr = test;
        } else {
            dsp = new DynamicShortestPath();
            ttr = dsp;
        }

        SimulationMain sim = new SimulationMain(ttr);

        //Changing the timestep to be 0.1s (100ms)
        conn.addOption("step-length", "0.1");
        conn.addOption("device.rerouting.probability", "1.0");
        conn.addOption("routing-algorithm", "dijkstra");

        try{
            //Start Traci
            conn.runServer();
            //Initialise the simulation & load routers + vehicles
            conn.do_timestep();

            if(TESTING) {
                test.beforeLoop();
            } else {
                dsp.beforeLoop();
            }

            //Running for the duration of the simulation
            for(int i = START_TIME; i < END_TIME; i++){
                if(TESTING) {
                    test.duringLoop(i);
                } else {
                    dsp.duringLoop(i);
                }
            }

            //Close TraCI connection
            conn.close();
        }catch (Exception e) {
            e.printStackTrace();
        }
    }

    protected void setConn(SumoTraciConnection conn) {
        this.conn = conn;
    }

    //Returns the current time of the simulation in ms
    public static int getCurrentTime() throws Exception {
        return (Integer) conn.do_job_get(Simulation.getCurrentTime());
    }



}
