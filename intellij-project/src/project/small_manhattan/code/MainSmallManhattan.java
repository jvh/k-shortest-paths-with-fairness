package project.southampton.code;

import it.polito.appeal.traci.SumoTraciConnection;

public class MainSmallManhattan {

    public static final String NORMAL_CONFIG = "src/project/configuration_files/config.cfg";
    public static final String LITE_CONFIG = "src/project/configuration_files/config_lite.cfg";
    public static final String TEST_CONFIG = "src/project/configuration_files/config_test.cfg";

    static String sumo_bin = "D:/Program Files/SUMO/bin/sumo-gui.exe";
    static final String config_file = TEST_CONFIG;


    public static void main(String[] args) {

        //start Simulation
        SumoTraciConnection conn = new SumoTraciConnection(sumo_bin, config_file);

        //set some options
        conn.addOption("step-length", "0.1"); //timestep 100 ms

        try{

            //start TraCI
            conn.runServer();

            //load routes and initialize the simulation
            conn.do_timestep();

//            Collection<Vehicle> vehicles = conn.

            for(int i=0; i<3600; i++){
                conn.do_timestep();
            }

            //stop TraCI
            conn.close();

        }catch(Exception ex){ex.printStackTrace();}

    }

}
