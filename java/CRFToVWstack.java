/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

import java.io.*;
import java.util.ArrayList;
import java.util.HashMap;

/**
 *
 * @author jun
 */
public class CRFToVWstack {

    /**
     * @param args the command line arguments
     */

    public static void main(String[] args) {
        
        String LFile = "data/i2b2/bioDeid_i2b2_vw.txt";
        HashMap<String, String> lMap = new HashMap<>();
        readLFile(LFile, lMap);
                
        String dmA[] = {"train", "test"};
        String dataA[] = {"04", "06", "14", "16"};
                        
        for (String dm : dmA) {
            String dmS = "tr";            
            if (dm.equals("test")) {
                dmS = "ts";
            }
        
            for (String data : dataA) {
                String inFile = "data/vowpal_wabbit/test/deid_stack_new/deid" + data + "_fv_" + dmS + "_f_st.txt";
                String outFile = "data/vowpal_wabbit/test/deid_stack_new/deid" + data + "_fv_" + dmS + "_f_vw.txt";
                
                ArrayList<String> lbls = new ArrayList<>();
                ArrayList<ArrayList<String>> insts = new ArrayList<>();
                readInst(inFile, lbls, insts, lMap);

                ArrayList<String> outs = new ArrayList<>();
                makeFv(lbls, insts, outs);
                writeFile(outFile, outs);                
            }
        }
        
    }

    public static void makeFv(ArrayList<String> lbls, 
            ArrayList<ArrayList<String>> insts, ArrayList<String> outs) {
        
        //17 |w Record date  2135-07-10 |v 696 119 364 <n>7 |d 0
        for (int i = 0; i < insts.size(); i++) {
            
            int win = 2;
            
            if (lbls.get(i).isEmpty()) {
                outs.add("");
                continue;
            }
                    
            StringBuilder sb = new StringBuilder();
            sb.append(lbls.get(i) + " ");

            // 04 06 14 16
            // 1 2 3 4
            append(sb, "w", 1, insts, i);
            append(sb, "x", 2, insts, i);
            append(sb, "y", 3, insts, i);
            append(sb, "z", 4, insts, i);

            appendP(sb, "a", win, 1, insts, i);
            appendP(sb, "b", win, 2, insts, i);
            appendP(sb, "c", win, 3, insts, i);
            appendP(sb, "d", win, 4, insts, i);
            
            appendN(sb, "a", win, 1, insts, i);
            appendN(sb, "b", win, 2, insts, i);
            appendN(sb, "c", win, 3, insts, i);
            appendN(sb, "d", win, 4, insts, i);

            outs.add(sb.toString().trim());
        }
    }
    
    public static void append(StringBuilder sb, String prefix,
            int idx, ArrayList<ArrayList<String>> insts, int cur) {
        
        sb.append("|" + prefix + " ");
        sb.append(insts.get(cur).get(idx) + " ");
    }    
    
    public static void appendP(StringBuilder sb, String prefix, int range, 
            int idx, ArrayList<ArrayList<String>> insts, int cur) {
        
        int min = Math.max(0, cur - range);
        sb.append("|" + prefix + "p ");
        String str = "";
        for (int i = cur; i >= min; i--) {
            if (insts.get(i) == null) {
                break;
            }
            if (i == cur) {
                str = insts.get(i).get(idx);                
            } else {
                str = insts.get(i).get(idx) + " " + str;
            }
        }        
        sb.append(str + " ");
    }
    
    public static void appendN(StringBuilder sb, String prefix, int range, 
            int idx, ArrayList<ArrayList<String>> insts, int cur) {
        
        int max = Math.min(cur + range, insts.size() - 1);
        sb.append("|" + prefix + "n ");
        String str = "";
        for (int i = cur; i <= max; i++) {
            if (insts.get(i) == null) {
                break;
            }
            str += insts.get(i).get(idx) + " ";               
        }        
        sb.append(str);
    }
    
    public static void readInst(String fileName, ArrayList<String> lbls, 
            ArrayList<ArrayList<String>> insts, HashMap<String, String> lMap) {

        String str = "";
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(fileName));
                while ((str = txtin.readLine()) != null) {
                    if (str.trim().isEmpty()) {
                        lbls.add("");
                        insts.add(null);                   
                    } else {
                        String s[] = str.split("\t");
                        if (!lMap.containsKey(s[s.length - 1])) {
                            System.out.println("wrong label mapping!!!!: " + s[s.length - 1]);
                        }
                        lbls.add(lMap.get(s[s.length - 1]));
                        ArrayList<String> tmp = new ArrayList<>();
                        for (int i = 0; i < s.length - 1; i++) {
                            //bar, colon, space, and newline.
                            tmp.add(s[i].replace("|", "[-b-]").replace(":", "[-c-]").replace(" ", "[-s-]"));
                        }
                        insts.add(tmp);
                    }
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
    
    public static void readLFile(String fileName, HashMap<String, String> map) {

        String str = "";
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(fileName));
                while ((str = txtin.readLine()) != null) {
                    //O	19
                    String s[] = str.split("\t");
                    map.put(s[0], s[1]);
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
    
    public static PrintWriter getPrintWriter (String file)
    throws IOException {
        return new PrintWriter (new BufferedWriter
                (new FileWriter(file)));
    }

    public static void writeFile(String name, ArrayList<String> inst) {

        try {

            PrintWriter out = getPrintWriter(name);
            for (String str: inst) {
                out.println(str);
            }
            out.flush();
            out.close();
        } catch (IOException e) {
            e.printStackTrace ();
        }
        //System.out.println(idx.size());
    }
}

