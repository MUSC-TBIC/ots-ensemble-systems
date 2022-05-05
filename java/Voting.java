/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */



import java.io.*;
import java.util.ArrayList;
import java.util.TreeMap;
import java.util.TreeSet;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Document.OutputSettings;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

/**
 *
 * @author jun
 */
public class Voting {

    /**
     * @param args the command line arguments
     * dependency: jsoup (https://github.com/jhy/jsoup/releases/tag/jsoup-1.6.2)
     */

    public static void main(String[] args) {
        
        int th = Integer.parseInt(args[0]);
        
        String txtDir = args[1]; // xml files
        String outDir = args[2];

        File oDir = new File(outDir);
        if (!oDir.exists()) {
            oDir.mkdirs();
        }
                
        // add input systems
        ArrayList<String> inDirs = new ArrayList<String>();
        for (int i = 3; i < args.length; i++) {
            if (args[i] == null || args[i].trim().isEmpty()) {
                continue;
            }
            
            File f = new File(args[i]);
            if (!f.exists()) {
                System.out.println("directory not exist: " + args[i]);
                continue;
            }
            inDirs.add(args[i]);
        }
        
        // list text files
        ArrayList<String> fileList = new ArrayList<String>();
        listFile(txtDir, fileList);
        
        //vote
        for (String fileName : fileList) {
            ArrayList<TreeMap<String, String>> instList = new ArrayList<TreeMap<String, String>>();
            
            for (String inDir : inDirs) {
                TreeMap<String, String> instMap = new TreeMap<String, String>();
                
                getCons(inDir, fileName, instMap);
                instList.add(instMap);
            }
            vote(th, outDir, fileName, instList, txtDir);
        }

    }
    
    public static void vote(int th, String outDir, String fileName, 
            ArrayList<TreeMap<String, String>> instList, String txtDir) {
        
        TreeMap<String, String> maps = new TreeMap<String, String>();
        TreeMap<String, Integer> cnts = new TreeMap<String, Integer>();
        TreeMap<String, Integer> orders = new TreeMap<String, Integer>();
        
        ArrayList<String> inst = new ArrayList<String>();
        
        for (int i = 0; i < instList.size(); i++) {
            eachVote(th, i, maps, cnts, orders, instList);
        }
        overlap(maps, cnts, orders, inst);
                    
        writeListFile(fileName, inst, txtDir, outDir);
                
    }
        
    public static void eachVote(int th, int idx,
            TreeMap<String, String> maps,
            TreeMap<String, Integer> cnts,
            TreeMap<String, Integer> orders,
            ArrayList<TreeMap<String, String>> instList) {
        
        TreeMap<String, String> map = instList.get(idx);
        
        for (String key: map.keySet()) {
            
            int vCnt = 1;
            for (int i = 0; i < instList.size(); i++) {
                
                if (i == idx) {
                    continue;
                }
                if (instList.get(i).containsKey(key)) {
                    instList.get(i).remove(key);
                    vCnt++;
                }
            }
            
            if (vCnt >= th) {
                if (!maps.containsKey(key)) {
                    maps.put(key, map.get(key));
                    cnts.put(key, vCnt);
                    orders.put(key, idx);
                }
            }
        }
    }
    
    /* check overlap
     * if no overlap, add
     * else if overlap,
     *  if highest vote count, add
     *  else if same votes exist,
     *    choose the highest priority, add
     */
    
    public static void overlap(
    TreeMap<String, String> maps,
    TreeMap<String, Integer> cnts,
    TreeMap<String, Integer> orders,
    ArrayList<String> inst
    ) { 
        
        TreeMap<String, String> tmp = new TreeMap<String, String>();
        tmp.putAll(maps);
        
        TreeSet<String> done = new TreeSet<String>();
        
        TreeMap<String,String> spanMap = new TreeMap<String,String>(new SpanMapComp());
        for (String key : maps.keySet()) {
            spanMap.put(key, maps.get(key));
        }
        
        for (String key : spanMap.keySet()) {
            
            if (done.contains(key)) {
                continue;
            }
            String keyA[] = key.split(" ");
            
            int s = Integer.parseInt(keyA[0]);
            int e = Integer.parseInt(keyA[1]);
            
            TreeSet<Integer> rs = new TreeSet<Integer>();
            for (int i = s; i < e; i++) {
                rs.add(i);
            }
            
            int order = orders.get(key);
            // collect overlap concepts
            TreeMap<String, String> overs = new TreeMap<String, String>();
            for (String key2 : tmp.keySet()) {
            
                if (key.equals(key2)) {
                    continue;
                }
                if (done.contains(key2)) {
                    continue;
                }
                
                String keyA2[] = key2.split(" ");
            
                int s2 = Integer.parseInt(keyA2[0]);
                int e2 = Integer.parseInt(keyA2[1]);
            
                boolean ifOverlap = false;
                for (int i = s2; i < e2; i++) {
                    if (rs.contains(i)) {
                        ifOverlap = true;
                        break;
                    }
                }
                if (ifOverlap) {
                    overs.put(key2, tmp.get(key2));
                }
            } // for tmp
            
            if (overs.isEmpty()) {
                // no overlap concept
                inst.add(maps.get(key));
                done.add(key);
            } else {
                //System.out.println(overs.size());
                
                // collect overlap with same vote
                TreeSet<String> oSet = new TreeSet<String>();
                int cnt = cnts.get(key);
                boolean ifMost = true;
                for (String key3: overs.keySet()) {
                    int cnt3 = cnts.get(key3);
                    
                    if (cnt < cnt3) {
                        ifMost = false;
                    } else if (cnt == cnt3) {
                        oSet.add(key3);
                    } 
                }
                
                if (ifMost) {
                    // if no concept with same vote
                    if (oSet.isEmpty()) {
                        inst.add(maps.get(key));
                        done.add(key);
                        
                        for (String key4: overs.keySet()) {
                            done.add(key4);
                        }
                        
                    } else {
                    // if there are concepts with same vote    
                        // by order
                        boolean ifLower = true;
                        for (String key4: oSet) {
                            int pri = orders.get(key4);

                            if (order > pri) {
                                ifLower = false;
                            }
                        }

                        if (ifLower) {
                            inst.add(maps.get(key));
                            done.add(key);

                            for (String key4: oSet) {
                                done.add(key4);
                            }
                        }
                    }
                    // if most
                } else {
                    done.add(key);
                }// if not most                
            }// if overs is not empty
            
        }// for maps
        
    }
    
    public static void listFile(String dirName, ArrayList<String> fileList) {
        File dir = new File(dirName);

        String[] children = dir.list();
        if (children == null) {
            return;
        } else {
            for (String filename : children) {
                if (filename.endsWith(".xml")) {
                    fileList.add(filename);
                }
            }
        }

    }

    public static void getCons(String inDir, String fileName, TreeMap<String, String> map) {
    
        File f = new File(inDir, fileName);
        if (!f.exists()) {
            return;
        }
                
        String str;
        StringBuilder sb = new StringBuilder();
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(new File(inDir, fileName)));

                while ((str = txtin.readLine()) != null) {
                    sb.append(str).append("\n");
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
        
        OutputSettings settings = new Document.OutputSettings();
        settings.prettyPrint(false);
        
        Document document = Jsoup.parse(sb.toString());
        
        Element deIdi2b2 = document.getElementsByTag("deIdi2b2").first();
        Element tags = deIdi2b2.getElementsByTag("TAGS").first();
        
        if (tags == null) {
            System.out.println("null");
        } else {
            Elements ts = tags.children();
            for (Element t : ts) {
                //System.out.println(t.toString());
                String start = t.attr("start");
                String end = t.attr("end");
                String type1 = t.attr("type");
                String cType = t.tagName().toUpperCase();               
                String outStr = "<" + cType + " id=\"P0\" start=\"" + start + "\" end=\"" + end + "\" TYPE=\"" + type1 + "\"" + " text=\"\" />";
                map.put(start + " " + end + " " + type1, outStr);
            }
        }
    }
    
    public static void readTxtFile(String dir, String file, ArrayList<String> inst) {

        String str = "";
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(new File(dir, file)));

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
    
    public static PrintWriter getPrintWriter (String dir, String file)
    throws IOException {
        return new PrintWriter (new BufferedWriter
                (new FileWriter(new File(dir, file))));
    }

    public static void writeListFile(String name, ArrayList<String> outs, String txtDir, String outDir) {

        ArrayList<String> txts = new ArrayList<String>();
        readTxtFile(txtDir, name, txts);

        try {
            PrintWriter out = getPrintWriter(outDir, name);
            
            for (String t : txts) {
                out.println(t);
            }
            out.println("<TAGS>");
            
            int id = 0;
            for (String t : outs) {
                out.println(t.replaceFirst(" id=\"P[0-9]+\" start=", " id=\"P" + id + "\" start="));
                id++;
            }
            out.println("</TAGS>\n</deIdi2b2>");
            out.flush();
            out.close();
        } catch (IOException e) {
            e.printStackTrace ();
        }
    }
}
