package project.small_manhattan.code;

import it.polito.appeal.traci.SumoTraciConnection;

public abstract class TestToRun {

    abstract void beforeLoop() throws Exception;
    abstract void duringLoop(int i) throws Exception;
    abstract SumoTraciConnection getConn() throws Exception;

}
