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
public class voteSearch {

    /**
     * @param args the command line arguments
     */

    public static void main(String[] args) {
        
        String dm = "train";
        args = new String[100];
        
        String dir = "data/i2b2/2016deid/" + dm + "/";
        args[0] = "2016";
        args[1] = "";
        args[2] = dir + "xml/";
        args[3] = dir + "con_vote_1416_16_prune/";
        String vDir = args[3];

        int j = 4;

        args[j++] = dir + "con_rnn_16_16/";
        args[j++] = dir + "con_neuXml_16_16/";
        args[j++] = dir + "con_soft_16_16/";
        args[j++] = dir + "con_vw_16_16/";
        args[j++] = dir + "con_srn_16_16/";
        args[j++] = dir + "con_lib_16_16/";
        args[j++] = dir + "con_crf_16_16/";
        args[j++] = dir + "con_mira_16_16/";
        args[j++] = dir + "con_memm_16_16/";
        args[j++] = dir + "con_neuXml_14_16/";
        args[j++] = dir + "con_mitie_16_16/";
        args[j++] = dir + "con_lib_14_16/";
        args[j++] = dir + "con_srn_14_16/";
        args[j++] = dir + "con_vw_14_16/";
        args[j++] = dir + "con_mira_14_16/";
        args[j++] = dir + "con_crf_14_16/";
        args[j++] = dir + "con_memm_14_16/";
        args[j++] = dir + "con_rnn_14_16/";
        args[j++] = dir + "con_soft_14_16/";
        args[j++] = dir + "con_mitie_14_16/";
        args[j++] = dir + "con_mistXml/";
        args[j++] = dir + "con_physioXml/"; 
        
        String year = args[0];
        
        String txtDir = args[2];
        String outDir = args[3];

        File oDir = new File(outDir);
        if (oDir.exists()) {
            oDir.delete();
        }
        oDir.mkdir();


        // list text files
        ArrayList<String> fileList = new ArrayList<String>();
        listFile(txtDir, fileList);

        ArrayList<String> inDirFinal = new ArrayList<String>();       
        double finalF1 = 0.0;
        int finalTh = 2;
        
        for (int thI = 2; thI <= 22; thI++) {
            int th = thI; //Integer.parseInt(args[1]);
            System.out.println("[ " + thI + " ]---------------------------");

            // add input systems
            ArrayList<String> inDirs = new ArrayList<String>();
            for (int i = 4; i < args.length; i++) {
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
            
            double f1 = getF1(outDir, fileList, inDirs, th, txtDir, year);

            ArrayList<String> inDirsCopy = new ArrayList<String>();
            inDirsCopy.addAll(inDirs);

            double maxF1 = f1;
            String maxDir = "";
            while (true) {

                for (String in : inDirs) {
                    inDirsCopy.clear();
                    inDirsCopy.addAll(inDirs);
                    inDirsCopy.remove(in);
                    double f1s = getF1(outDir, fileList, inDirsCopy, th, txtDir, year);
                    if (f1s > maxF1) {
                        maxF1 = f1s;
                        maxDir = in; 
                    }
                }
                System.out.println(maxF1 + " " + maxDir);
                // if every classifer helps, stop
                if (maxF1 <= f1 ) {
                    break;
                }
                f1 = maxF1;
                inDirs.remove(maxDir);
                System.out.println("\n---------------------------");
            }

            System.out.println("\n---------------------------");
            System.out.println(inDirs.size());
            for (String in : inDirs) {
                System.out.println(in);
            }

            f1 = getF1(outDir, fileList, inDirs, th, txtDir, year);
            
            if (finalF1 < f1) {
                inDirFinal.clear();
                inDirFinal.addAll(inDirs);                
                finalF1 = f1;
                finalTh = th;
            }
            
        }

        System.out.println("\n---------------------------");
        System.out.println("\n---------------------------");
        System.out.println("\n---------------------------");
        System.out.println("[th: " + finalTh + " ] " + inDirFinal.size());
        for (String in : inDirFinal) {        
            System.out.println(in);            
        }
        
        getF1(outDir, fileList, inDirFinal, finalTh, txtDir, year);
        
    }
    
    public static double getF1(String outDir, ArrayList<String> fileList, 
            ArrayList<String> inDirs, int th, String txtDir, String year) {
        
        File oDir = new File(outDir);
        if (oDir.exists()) {
            oDir.delete();
        }
        oDir.mkdir();

        //vote
        for (String fileName : fileList) {
            ArrayList<TreeMap<String, String>> instList = new ArrayList<TreeMap<String, String>>();

            for (String inDir : inDirs) {
                TreeMap<String, String> instMap = new TreeMap<String, String>();

                getCons(inDir, fileName, instMap, year);
                instList.add(instMap);
            }
            vote(th, outDir, fileName, instList, txtDir);
        }

        Eval.test(txtDir, outDir, year);
        System.out.println(Eval.getF1());
        
        return Eval.getF1();
        
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
     if no overlap, add
     if overlap,
     *  if highest vote count, add
     * 
     *  if same votes exist,
     *      if highest priority, add
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
                        /*        
                        if (oSet.size() >=2) {
                            System.out.println(oSet.size());
                        }
                        */
                        
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

    public static void getCons(String inDir, String fileName, TreeMap<String, String> map, String year) {
    
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
                //<DATE id="P0" start="16" end="26" text="2069-04-07" TYPE="DATE" comment="" />
                String outStr = "<" + cType + " id=\"P0\" start=\"" + start + "\" end=\"" + end + "\" TYPE=\"" + type1 + "\"" + " text=\"\" />";
                map.put(start + " " + end + " " + type1, outStr);
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

    public static void writeListFile(String name, ArrayList<String> outs, String txtDir, String outDir) {

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
            out.println("</TAGS>\n</deIdi2b2>");
            out.flush();
            out.close();
        } catch (IOException e) {
            e.printStackTrace ();
        }
        //System.out.println(idx.size());
    }
}
