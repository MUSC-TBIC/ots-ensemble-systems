/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

import java.io.*;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.TreeMap;
import java.util.TreeSet;

/**
 *
 * @author jun
 */
public class StackFeature {

    /**
     * @param args the command line arguments
     */

    public static void main(String[] args) {

        String fFile = "";
        String inFile = "";
        String outFile = "";
        
        fFile = args[0];
        inFile = args[1];
        outFile = args[2];
        
        TreeSet<Integer> set = new TreeSet<Integer>();
        
        readFeature(fFile, set);
        
        
        ArrayList<String> inst = new ArrayList<String>();
        
        readInst(inFile, inst, set);

        System.out.println(inst.size());
        
        writeFile(outFile, inst);
        
    }
    //reads in file and store them to inst
    public static void readInst(String fileName, ArrayList<String> inst, TreeSet<Integer> set) {

        File f = new File(fileName);
        
        String str = "";
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(fileName));

                while ((str = txtin.readLine()) != null) {
                    //0 2:1.0 4:1.0 6:1.0 8:1.0 10:1.0 12:1.0 14:1.0 16:1.0 182:1.0 192:1.0 
                	//strA - line
                    String strA[] = str.split(" ");
                    String label = strA[0];
                    StringBuilder sb = new StringBuilder();
                    //sb LABEL + " "
                    sb.append(label + " ");
                    for (int i = 1; i < strA.length; i++) {
                        String tStrA[] = strA[i].split(":");
                        int idx = Integer.parseInt(tStrA[0]);
                        double val = Double.parseDouble(tStrA[1]);
                        if (set.contains(idx) && val != 0 ) {
                            sb.append(strA[i] + " ");
                        }
                    }
                    //isnt a list of sb
                    inst.add(sb.toString().trim());
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
    //add count from file to set
    public static void readFeature(String fileName, TreeSet<Integer> set) {

        File f = new File(fileName);
        
        String str = "";
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(fileName));

                while ((str = txtin.readLine()) != null) {
                    if (!str.contains(" ")) {
                        continue;
                    } 
                    if (str.startsWith("#")) {
                        continue;
                    }                    
                    String strA[] = str.split(" ");
                    int s = Integer.parseInt(strA[0]);
                    int e = Integer.parseInt(strA[1]);
                    //set a set of numbers in strA
                    for (int i = s; i <= e; i++) {
                        set.add(i);
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
        
    public static PrintWriter getPrintWriter (String file)
    throws IOException {
        return new PrintWriter (new BufferedWriter
                (new FileWriter(file)));
    }
    //write inst to output file
    public static void writeFile(String name, ArrayList<String> inst) {

        try {

            PrintWriter out = getPrintWriter(name);
            for (String str : inst) {
                out.println(str);
            }
            out.flush();
            out.close();
        } catch (Exception e) {
            e.printStackTrace ();
        }
        //System.out.println(idx.size());
    }
}
