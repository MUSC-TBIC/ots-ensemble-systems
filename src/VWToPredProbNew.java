/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

import java.io.*;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.TreeMap;

/**
 *
 * @author jun
 */
public class VWToPredProbNew {

    /**
     * @param args the command line arguments
     */

    public static void main(String[] args) {

        String inFileR = "";
        String inFileA = "";
        String lMapFile = "";
        
        inFileR = args[0];
        inFileA = args[1];
        lMapFile = args[2];
        
        TreeMap <String, String> conMap = new TreeMap <String, String>();
        readLabelR(lMapFile, conMap);

        TreeMap<Integer, Integer> sMap = new TreeMap<Integer, Integer>();
        TreeMap<Integer, String> trace = new TreeMap<Integer, String>();
                
        ArrayList<String> instR = new ArrayList<String>();
        ArrayList<String> instA = new ArrayList<String>();
        readInstR(inFileR, instR, sMap, trace);
        readInstA(inFileA, instA, conMap, sMap, trace);

        correct(instR, instA);
        
        writeFile(inFileA, instR, instA);

    }

    public static void readLabelR(String fileName, TreeMap <String, String> map) {

        String str = "";
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(fileName));

                while ((str = txtin.readLine()) != null) {
                    String strA[] = str.split("\t", 2);
                    map.put(strA[1], strA[0]);
                }
            } catch (Exception ex) {
                ex.printStackTrace();
            } finally {
                try {
                    txtin.close();
                } catch (Exception ex) {

               }
            }
        }

    }

    public static void readInstR(String fileName, ArrayList<String> inst, 
            TreeMap<Integer, Integer> sMap, TreeMap<Integer, String> trace) {

        String str = "";
        {
            BufferedReader txtin = null;
            int cnt = 0;
            int sN = 0;
            try {
                txtin = new BufferedReader(new FileReader(fileName));
                
                String pStr = "";
                while ((str = txtin.readLine()) != null) {
                    inst.add(str);
                    if (!str.trim().isEmpty()) {
                        cnt++;
                    } else {
                        sMap.put(sN, cnt);
                        trace.put(sN, pStr);
                        sN++;
                        cnt = 0;
                    }
                    pStr = str;
                }
                System.out.println(cnt);
            } catch (Exception ex) {
                ex.printStackTrace();
            } finally {
                try {
                    txtin.close();
                } catch (Exception ex) {

               }
            }
        }

    }

    public static void readInstA(String fileName, ArrayList<String> inst, TreeMap <String, String> conMap
            , TreeMap<Integer, Integer> sMap, TreeMap<Integer, String> trace) {

        String str = "";
        {
            BufferedReader txtin = null;
            
            try {
                txtin = new BufferedReader(new FileReader(fileName));
                int sN = 0;
                while ((str = txtin.readLine()) != null) {
                    String strA[] = str.trim().split(" ");
                    for (String s : strA) {
                        inst.add(conMap.get(s));
                    }
                    if (sMap.get(sN) != strA.length) {
                        System.out.println("mismatch: " + sN + " " + sMap.get(sN) + " " + strA.length);
                        System.out.println(trace.get(sN));
                        break;
                    }
                    sN++;
                }
                System.out.println(inst.size());
            } catch (Exception ex) {
                ex.printStackTrace();
            } finally {
                try {
                    txtin.close();
                } catch (Exception ex) {

               }
            }
        }

    }
    
    public static PrintWriter getPrintWriter (String file)
    throws IOException {
        return new PrintWriter (new BufferedWriter
                (new FileWriter(file)));
    }

    public static void correct(ArrayList<String> instR,
            ArrayList<String> tags) {

        System.out.println(instR.size());
        System.out.println(tags.size());
        
        ArrayList<String> out = new ArrayList<>();
        int idx = 0;

        for (int i = 0; i < instR.size(); i++) {
            if (!instR.get(i).trim().isEmpty()) {
                out.add(tags.get(i-idx));
            } else {
                out.add("skip");
                idx++;
            }
        }
        
        tags.clear();
        tags.addAll(out);        
    
        String cTag = "O";
        String nTag = "O";
        String cType = "O";
        String nType = "O";

        for (int i = 0; i < tags.size(); i++) {
        
            cTag = tags.get(i);
            
            if (cTag.equals("skip")) {
                continue;
            }
            
            if (i < tags.size() - 1) {
                nTag = tags.get(i + 1);
            } else {
                nTag = "O";
            }
            if (nTag.equals("skip")) {
                nTag = "O";
            }
                    
            if (!cTag.equals("O")) {
                cType = cTag.replace("B-","").replace("I-", "");
            } else {
                cType = "O";
            }
            if (!nTag.equals("O")) {
                nType = nTag.replace("B-","").replace("I-", "");
            } else {
                nType = "O";
            }        
            
            if (cTag.startsWith("B-")) {
                if (nTag.startsWith("I-")) {
                    if (!cType.equals(nType)) {
                        tags.set(i + 1, "I-" + cType);
                    }
                } 
            } else if (cTag.startsWith("I-")) {
                if (nTag.startsWith("I-")) {
                    if (!cType.equals(nType)) {
                        tags.set(i + 1, "I-" + cType);
                    }
                }                
            } else if (cTag.equals("O") && nTag.startsWith("I-")) {
                tags.set(i + 1, "O");
            } 
        }
    }    
    
    public static void writeFile(String name, ArrayList<String> instR,
            ArrayList<String> instA) {

        try {

            PrintWriter out = getPrintWriter(name);
            for (int i = 0; i < instR.size(); i++) {
                if (!instR.get(i).trim().isEmpty()) {
                    out.println(instR.get(i) + "\t" + instA.get(i) + "\t1.0");
                } else {
                    out.println("");
                }
            }
            out.flush();
            out.close();
        } catch (Exception e) {
            e.printStackTrace ();
        }
        //System.out.println(idx.size());
    }
}