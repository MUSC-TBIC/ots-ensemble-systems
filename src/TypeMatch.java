/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

import java.io.*;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.TreeMap;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

/**
 *
 * @author jun
 */
public class TypeMatch {

    
    public static void main(String[] args) {

        String mapDir = "data/i2b2/i2b2_deid/map/";
        
        String cs[] = {"04", "06", "14", "16"}; 
        String years[] = {"2014", "2014", "2014", "2016"};

        for (int i = 0; i < cs.length; i++) {
            String cR = cs[i]; // test data
            String refDir = "data/i2b2/20" + cR + "deid/train/xml/";
            String yR = years[i];

            ArrayList<String> fileList = new ArrayList<String>();
            // list dir
            listFile(refDir, fileList);
            
            for (int j = 0; j < cs.length; j++) {
                if (i == j) {
                    continue;
                }
                String cA = cs[j]; // system output, model
                String ansDir = "data/i2b2/20" + cR + "deid/train/con_rnnE_" + cA + "_" + cR + "_ne_nf/";
                String yA = years[j];

                System.out.println("ans: " + cA + " ref: " + cR + " year: " + yA + " " + yR);
                
                HashMap<String, HashMap<String, Integer>> mM = new HashMap<String, HashMap<String, Integer>>();
                // ans ref cnt
                // parse each file
                for (int k = 0; k < fileList.size(); k++) {
                    String fileName = fileList.get(k);
                    HashMap<Integer, String> rC = new HashMap<Integer, String>();
                    readRef(refDir, fileName, rC, yR);
                    readAns(ansDir, fileName, rC, mM, yA);
                }

                TreeMap<String, String> mT = new TreeMap<>();
                for (String k : mM.keySet()) {
                    int max = -1;
                    String mC = "";

                    HashMap<String, Integer> m = mM.get(k);
                    int tot = 0;
                    for (String k2 : m.keySet()) {
                        // ans ref
                        //System.out.println(k + "\t" + k2 + "\t" + m.get(k2));
                        int c = m.get(k2);
                        if (max < c) {
                            max = c;
                            mC = k2;
                        }
                        tot += c;
                    }
                    System.out.println(k + "\t" + mC + "\t" + max + "\t" + tot);
                    
                    mT.put(k, mC);
                }

                // header
                System.out.println("Ans" + "\t" + "Ref");
                //06 04
                //CITY	HOSPITAL
                // convert CITY (06 model output) to HOSPITAL for 04 test data
                for (String k : mT.keySet()) {
                    System.out.println(k + "\t" + mT.get(k));
                }        
                // save to file
                // model _ data
                // model schema, data schema
                writeMap(mapDir, cA + "_" + cR + ".txt", mT);
            }        
        }

    }

    public static void listFile(String dirName, ArrayList<String> fileList) {
        File dir = new File(dirName);

        String[] children = dir.list();
        if (children == null) {
            return;
        } else {
            for (int i = 0; i < children.length; i++) {
                // Get filename
                String filename = children[i];
                if (filename.endsWith(".xml")) {
                    fileList.add(filename);
                }
            }
        }

    }
    
    public static void readRef(String dir, String file, HashMap<Integer, String> rC, String year) {
    
        File f = new File(dir, file);
        if (!f.exists()) {
            return;
        }
                
        String strA;
        StringBuilder sb = new StringBuilder();
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(dir + file));

                while ((strA = txtin.readLine()) != null) {
                    sb.append(strA).append("\n");
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
        
        Document.OutputSettings settings = new Document.OutputSettings();
        settings.prettyPrint(false);
        
        Document document = Jsoup.parse(sb.toString());
        
        Element deIdi2b2;
        if (year.equals("2016")) {
            //System.out.println("2016");            
            deIdi2b2 = document.getElementsByTag("NGRID_deId").first();     
        } else {
            deIdi2b2 = document.getElementsByTag("deIdi2b2").first();                 
        }
        
        Element tags = deIdi2b2.getElementsByTag("TAGS").first();
        
        if (tags == null) {
            System.out.println("null");
        } else {
            Elements ts = tags.children();
            for (Element t : ts) {
                //System.out.println(t.toString());
                int start = Integer.parseInt(t.attr("start"));
                int end = Integer.parseInt(t.attr("end"));
                String type1 = t.attr("type").toUpperCase();
                //String cType = t.tagName().toUpperCase();               
                
                for (int i = start; i < end; i++) {
                    rC.put(i, type1);
                }
                
            }
        }
        
    }
    
    public static void readAns(String dir, String file, HashMap<Integer, String> rC,
            HashMap<String, HashMap<String, Integer>> mM, String year) {
    
        File f = new File(dir, file);
        if (!f.exists()) {
            return;
        }
                
        String strA;
        StringBuilder sb = new StringBuilder();
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(dir + file));

                while ((strA = txtin.readLine()) != null) {
                    sb.append(strA).append("\n");
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
        
        Document.OutputSettings settings = new Document.OutputSettings();
        settings.prettyPrint(false);
        
        Document document = Jsoup.parse(sb.toString());
        
        Element deIdi2b2;
        if (year.equals("2016")) {
            //System.out.println("2016");            
            deIdi2b2 = document.getElementsByTag("NGRID_deId").first();     
        } else {
            deIdi2b2 = document.getElementsByTag("deIdi2b2").first();                 
        }
        
        Element tags = deIdi2b2.getElementsByTag("TAGS").first();
        
        ArrayList<String> outs = new ArrayList<String>();
        int id = 0;
        if (tags == null) {
            System.out.println("null");
        } else {
            Elements ts = tags.children();
            for (Element t : ts) {
                //System.out.println(t.toString());
                String start = t.attr("start");
                String end = t.attr("end");
                String type1 = t.attr("type").toUpperCase();
                String cType = t.tagName().toUpperCase();               
                outs.add(start + "|" + end + "|P" + id + "|" + type1 + "|" + cType + "|AAA");
                id++;
            }
        }
        
        for (String str : outs) {
            String sA[] = str.split("\\|" , 6);
            int s = Integer.parseInt(sA[0]);
            int e = Integer.parseInt(sA[1]);
            String t = sA[3];

            if (t.trim().isEmpty()) {
                System.out.println(str);
            }

            /* OLD
            for (int i = s; i < e; i++) {
                if (rC.containsKey(i)) {
                    String k = rC.get(i);

                    if (mM.containsKey(t)) {
                        HashMap<String, Integer> tmp = mM.get(t);
                        if (tmp.containsKey(k)) {
                            int v = tmp.get(k) + 1;
                            tmp.put(k, v);
                        } else {
                            tmp.put(k, 1);
                        }
                    } else {
                        HashMap<String, Integer> tmp = new HashMap<String, Integer>();
                        tmp.put(k, 1);
                        mM.put(t, tmp);
                    }
                    break;
                }
            }
            */     
            // new            
            HashSet<String> tSet = new HashSet<>();
            for (int i = s; i < e; i++) {
                if (rC.containsKey(i)) {
                    String k = rC.get(i);
                    if (!tSet.contains(k)) {
                        tSet.add(k);
                    }
                }
            }

            for (String k: tSet) {
                if (mM.containsKey(t)) {
                    HashMap<String, Integer> tmp = mM.get(t);
                    if (tmp.containsKey(k)) {
                        int v = tmp.get(k) + 1;
                        tmp.put(k, v);
                    } else {
                        tmp.put(k, 1);
                    }
                } else {
                    HashMap<String, Integer> tmp = new HashMap<String, Integer>();
                    tmp.put(k, 1);
                    mM.put(t, tmp);
                }                
            }
            // new
            
        }
    }    
    
    public static PrintWriter getPrintWriter (String file)
    throws IOException {
        return new PrintWriter (new BufferedWriter
                (new FileWriter(file)));
    }
    
    public static void writeMap(String dir, String fName, TreeMap<String, String> map) {

        try {
            PrintWriter out = getPrintWriter(dir + fName);
            for (String k : map.keySet()) {
                out.println(k + "\t" + map.get(k));
            }        
            out.flush();
            out.close();
        } catch (IOException e) {
            e.printStackTrace ();
        }
    }        
    
}
