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
public class RemOverlapDeid {

    /**
     * @param args the command line arguments
     */
    public static void main(String[] args) {
        
        String inDir = args[0];
        String txtDir = args[1];
        String year = args[2];
        
        // list text files
        TreeSet<String> fileList = new TreeSet<String>();
        listFile(inDir, fileList);
                
        for (String fileName : fileList) {
            
            TreeMap<String, String> instMap = new TreeMap<String, String>();
            TreeMap<String, Double> scoreMap = new TreeMap<String, Double>();
                
            getCons(inDir, fileName, instMap, scoreMap, year);
            ArrayList<String> inst = new ArrayList<String>();
            chk(instMap, scoreMap, inst);
            
            writeListFile(fileName, inst, txtDir, inDir, year);
        
        }
    }
    
    public static void chk(
            TreeMap<String, String> maps,
            TreeMap<String, Double> scores,  ArrayList<String> insts
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
            
            double score = scores.get(key);
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
                insts.add(maps.get(key));
                done.add(key);
            } else {
                // score comparision               
                boolean ifMost = true;
                for (String key3: overs.keySet()) {
                    double score3 = scores.get(key3);
                    
                    if (score < score3) {
                        ifMost = false;
                    }
                    
                    if (score == score3) {
                        System.out.println("same score: " + score);
                    }
                }
                
                if (ifMost) {
                    insts.add(maps.get(key));
                    done.add(key);
                        
                    for (String key4: overs.keySet()) {
                        done.add(key4);
                    }
                    // if most
                } else {
                    done.add(key);
                }// if not most                
            }// if overs is not empty
            
        }// for maps
        
    }

    
    public static void listFile(String dirName, TreeSet<String> fileList) {
        File dir = new File(dirName);

        String[] children = dir.list();
        if (children == null) {
            return;
        } else {
            for (int i = 0; i < children.length; i++) {
                // Get filename
                String filename = children[i];
                if (!fileList.contains(filename)) {
                    fileList.add(filename);
                }
            }
        }

    }

    public static void getCons(String inDir, String fileName, TreeMap<String, String> map,
            TreeMap<String, Double> scores, String year) {
    
        File f = new File(inDir, fileName);
        if (!f.exists()) {
            return;
        }
                
        String str;
        StringBuilder sb = new StringBuilder();
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(inDir + fileName));

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
                String start = t.attr("start");
                String end = t.attr("end");
                String type1 = t.attr("type").toUpperCase();
                String cType = t.tagName().toUpperCase();   
                
                double score = Double.parseDouble(t.attr("score"));
                
                String outStr = "<" + cType + " id=\"P0\" start=\"" + start + "\" end=\"" + end + "\" TYPE=\"" + type1 + "\"" + " text=\"\" />";
                map.put(start + " " + end + " " + type1, outStr);
                scores.put(start + " " + end + " " + type1, score);
            }
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
    
    public static PrintWriter getPrintWriter (String file)
    throws IOException {
        return new PrintWriter (new BufferedWriter
                (new FileWriter(file)));
    }

    public static void writeListFile(String name, ArrayList<String> outs, String txtDir, String outDir,
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
