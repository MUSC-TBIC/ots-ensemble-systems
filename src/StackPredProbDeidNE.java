/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

import java.io.*;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.TreeMap;

/**
 *
 * @author jun
 */
public class StackPredProbDeidNE {

    /**
     * @param args the command line arguments
     */

    public static void main(String[] args) {

        String inFile = args[0];
        String inLFile = args[1];
        String outDir = args[2];
        String txtDir = args[3];
        String year = args[4];
        String cFile = args[5];
        String tFile = args[6];
        
        HashMap<Integer, String> classMap = new HashMap<>();
        readClassfile(cFile, classMap);    
        
        HashMap<String, String> typeMap = new HashMap<>();
        readTypefile(tFile, typeMap);    
                
        ArrayList<String> cons = new ArrayList<String>();
        ArrayList<Integer> anss = new ArrayList<Integer>();
        ArrayList<String> probs = new ArrayList<String>();
        
        getCons(inLFile, cons);
        readInstA(inFile, anss, probs);

        System.out.println(cons.size() + " " + anss.size());
        
        outCons(outDir, txtDir, cons, anss, probs, year, classMap, typeMap);
        
    }
    
    
    public static void outCons(String outDir, String txtDir, ArrayList<String> cons, 
            ArrayList<Integer> anss, ArrayList<String> probs, String year, 
            HashMap<Integer, String> classMap, HashMap<String, String> typeMap) {

        TreeMap<String, ArrayList<String>> outs = new TreeMap<String, ArrayList<String>>();
        
        for (int i = 0; i < cons.size(); i++) {
            //classMap
            String type1 = classMap.get(anss.get(i));
            
            if (type1 == null || type1.equals("NONE")) {
                if (type1 == null) {
                    System.out.println("unknown PHI class: " + anss.get(i));
                }
                continue;
            }
            
            String cType = typeMap.get(type1);
            if (cType == null) {
                System.out.println("no matched tag for : " + type1);
            }                        
            
            //filename + " " + start + " " + end + " " + type1 + " " + cType + " " + prob;
            String str = cons.get(i);
            String strA[] = str.split(" ");

            String fileName = strA[0];
            String start = strA[1];
            String end = strA[2];
            
            String score = probs.get(i);

            String outStr = "<" + cType + " id=\"P0\" start=\"" + start + "\" end=\"" + end + "\" TYPE=\"" + type1 + "\"" + " score=\"" + score + "\" text=\"\" />";

            if (!outs.containsKey(fileName)) {
                ArrayList<String> insts = new ArrayList<String>();
                insts.add(outStr);
                outs.put(fileName, insts);
            } else {
                outs.get(fileName).add(outStr);
            }

        }
        
        for (String f : outs.keySet()) {
            writeFile(outDir, txtDir, f, outs.get(f), year);
        }
    }
    
    public static void readTxtFile(String file, ArrayList<String> inst) {

        String str = "";
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(file));

                while ((str = txtin.readLine()) != null) {
                    inst.add(str);
                    if (str.trim().endsWith("</TEXT>")) {
                        break;
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
    
    public static void getCons(String fileName, ArrayList<String> cons) {

        String str = "";
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(fileName));

                while ((str = txtin.readLine()) != null) {
                    cons.add(str);
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
        
    public static void readInstA(String fileName, ArrayList<Integer> inst, 
            ArrayList<String> probs) {

        String str = "";
        {
            BufferedReader txtin = null;
            
            DecimalFormat df = new DecimalFormat("#.######");
            
            try {
                txtin = new BufferedReader(new FileReader(fileName));
                
                str = txtin.readLine();
                
                String labels[] = str.replace("labels", "").trim().split(" ");
                
                //labels 0 1
                //1 0.3101 0.6899
                
                TreeMap<Integer, Integer> lMap = new TreeMap<Integer, Integer>();
                int idx = 0;
                for (String key : labels) {
                    int i = Integer.parseInt(key);
                    lMap.put(i, idx); // 0 is 0 (first)
                    idx++;
                }
                
                while ((str = txtin.readLine()) != null) {
                    String strA[] = str.split(" ");
                    
                    int label = Integer.parseInt(strA[0]); // answer
                    String prob = strA[lMap.get(label) + 1]; 
                    Double probD = Double.parseDouble(prob);

                    inst.add(label);
                    probs.add(df.format(probD));
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
    
    public static void readClassfile(String fileName, HashMap<Integer, String> map) {

        String str = "";
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(fileName));
                while ((str = txtin.readLine()) != null) {
                    String s[] = str.split("," , 2);
                    map.put(Integer.parseInt(s[1]), s[0]);
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
    
    public static void readTypefile(String fileName, HashMap<String, String> map) {

        String str = "";
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(fileName));
                while ((str = txtin.readLine()) != null) {
                    String s[] = str.split("," , 2);
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

    
                
    public static void writeFile(String outDir, String txtDir, String name, ArrayList<String> outs,
            String year) {

        String txtFile = txtDir + name;
        ArrayList<String> txts = new ArrayList<String>();
        readTxtFile(txtFile, txts);
            
        try {
            PrintWriter out = getPrintWriter(outDir + name);
            
            for (String t : txts) {
                out.println(t);
            }
            out.println("<TAGS>");
            
            int id = 0;
            for (String t : outs) {
                out.println(t.replaceFirst(" id=\"P[0-9]+\" start=", " id=\"P" + id + "\" start="));
                id++;
            }
            
            if (year.equals("2016")) {
                out.println("</TAGS>\n</NGRID_deId>");
            } else {
                out.println("</TAGS>\n</deIdi2b2>");
            }            
            
            out.flush();
            out.close();
        } catch (IOException e) {
            e.printStackTrace ();
        }
        //System.out.println(idx.size());
    }
}