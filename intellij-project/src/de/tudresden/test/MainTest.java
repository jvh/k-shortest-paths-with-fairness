package de.tudresden.test;
 
import de.tudresden.sumo.cmd.Simulation;
import de.tudresden.sumo.cmd.Vehicle;
import it.polito.appeal.traci.SumoTraciConnection;
 
public class MainTest {
 
    static String sumo_bin = "D:/Program Files/SUMO/bin/sumo-gui.exe";
//    static final String config_file = "src/de/tudresden/test/simulation_other_test/hellotest.sumo.cfg";
    static final String config_file = "src/de/tudresden/test/sim/config.sumo.cfg";
     
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
             
            for(int i=0; i<3600; i++){
             
                                //current simulation time
                                int simtime = (int) conn.do_job_get(Simulation.getCurrentTime());
 
                conn.do_job_set(Vehicle.add("veh"+(i+1), "car", "s1", simtime, 0, 13.8, (byte) 1));
                conn.do_timestep();
            }
             
            //stop TraCI
            conn.close();
             
        }catch(Exception ex){ex.printStackTrace();}
         
    }
 
}