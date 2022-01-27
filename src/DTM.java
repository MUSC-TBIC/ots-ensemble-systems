/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */



import java.io.*;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
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
public class DTM {

    /**
     * @param args the command line arguments
     */

    public static void main(String[] args) {
        
        // if true: weighted version
        boolean ifWeight = true;
        
        DecimalFormat fm = new DecimalFormat("00.00");
        // Sample contents:  i2b2_2014_type.txt
        // DOCTOR,NAME
        // PATIENT,NAME
        // USERNAME,NAME
        // PROFESSION,PROFESSION
        // CITY,LOCATION
        // ...
        String cMapFile = "types/i2b2_2014_type.txt";
        String daA[] = {"04", "06", "14", "16"};
        
        double thA[];
        // threshold for each model
        if (ifWeight) {
            thA = new double[]{0.5, 0.5, 0.5, 0.6}; // with weight      
        } else {
            thA = new double[]{0.7, 0.5, 0.6, 0.7}; // for no weight               
        }
        
        String dmA[] = {"train", "test"};
        
        String msA[][] = {{"04", "06", "14", "16"}, 
                          {"06", "14", "16", "04"},          
                          {"14", "16", "06", "04"},            
                          {"16", "14", "06", "04"}
        };
        
        HashMap<String, String> sm = new HashMap<String, String>();
        readMapFile(cMapFile, sm);

        for (int v = 0; v < daA.length; v++) {
            //"04", "06", "14", "16"
            String da = daA[v];
            //e.g., 0.7, 0.5, 0.6, 0.7 threshold value
            double th = thA[v];
            
            // for each ref type,  // classfier
            HashMap<String, HashMap<String, Double>> dps = new HashMap<>();            
            for (int w = 0; w < dmA.length; w++) {
                String dm = dmA[w];
                        
                args = new String[100];
                //FILE NAME
                String dir = "data/i2b2/20" + da + "deid/" + dm + "/";

                args[0] = dir + "xml/";
                args[1] = dir + "xml/";

                if (ifWeight) {
                    args[2] = dir + "con_dtmw_" + da + "_" + da + "_ne/"; // with weight
                } else {
                    args[2] = dir + "con_dtm_" + da + "_" + da + "_ne/"; // for no weight
                }

                int j = 3;                    
                //FILE SUFFIX
                String ms[] = msA[v];
                for (String m : ms) {
                    if (m.equalsIgnoreCase(da)) {
                        args[j++] = dir + "con_rnnE_" + m + "_" + da + "_ne/";
                    } else {
                        args[j++] = dir + "con_rnnE_" + m + "_" + da + "_ne_nf/";                        
                    }
                }

                String year = "2014";
                if (da.equalsIgnoreCase("16")) {
                    year = "2016";
                }
                
                if (w == 0) { // train
                    exec(args, true, year, dps, sm, th, ifWeight);
                    //System.out.println(da + " train is done");
                } else {
                    exec(args, false, year, dps, sm, th, ifWeight);
                    
                    HashMap<String, Double> sc = new HashMap<>();
                    String refDir = "data/i2b2/20" + da + "deid/" + dm + "/xml/";
                    String outDir = args[2];
                    String out = evalExt(refDir, outDir);
                    parse(out, sc, fm, 1); // exact          
                    System.out.print(da + "\t" + th + "\t" + fm.format(sc.get("p")) + "\t" + fm.format(sc.get("r"))+ "\t" + fm.format(sc.get("f")));
                    
                    out = evalExt(refDir, outDir);
                    parse(out, sc, fm, 2); // partial         
                    System.out.println("\t" + fm.format(sc.get("p")) + "\t" + fm.format(sc.get("r"))+ "\t" + fm.format(sc.get("f")));
                } 
            }  // train or test     
        } // data set
    }
    //PARSE THE OUT FILE
    public static void parse(String out, HashMap<String, Double> sc, DecimalFormat fm, int option) {

        String str = "";
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new StringReader(out));

                while ((str = txtin.readLine()) != null) {
                    if (option == 1) {
                        if (str.startsWith("Strict") || str.startsWith("0 Strict")) {
                            txtin.readLine(); // for -----
                            double p = Double.parseDouble(txtin.readLine().replace("Total", "").replace("Precision", "").trim()) * 100;
                            double r = Double.parseDouble(txtin.readLine().replace("Recall", "").trim()) * 100;
                            double f = Double.parseDouble(txtin.readLine().replace("F1", "").trim()) * 100;

                            //System.out.println("\t" + iter + "\t\t" + fm.format(p) + "\t" + fm.format(r) + "\t" + fm.format(f));

                            sc.put("p", p);
                            sc.put("r", r);
                            sc.put("f", f);

                            return;
                        }
                    } else {
                        if (str.startsWith("Binary Token") || str.startsWith("0 Binary Token")) {
                            txtin.readLine(); // for -----
                            double p = Double.parseDouble(txtin.readLine().replace("Total", "").replace("Precision", "").trim()) * 100;
                            double r = Double.parseDouble(txtin.readLine().replace("Recall", "").trim()) * 100;
                            double f = Double.parseDouble(txtin.readLine().replace("F1", "").trim()) * 100;

                            //System.out.println("\t" + iter + "\t\t" + fm.format(p) + "\t" + fm.format(r) + "\t" + fm.format(f));

                            sc.put("p", p);
                            sc.put("r", r);
                            sc.put("f", f);

                            return;
                        }
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
            
    public static String evalExt(String refDir, String ansDir) {

        String s = null;
        
        StringBuilder sb = new StringBuilder();
        
        try {
            Process p = Runtime.getRuntime().exec("python data/i2b2/2014deid/2016_CEGS_N-GRID_evaluation_scripts-master/evaluate.py track1 "
                                                  + refDir + " " + ansDir);

            BufferedReader stdInput = new BufferedReader(new 
                                                         InputStreamReader(p.getInputStream()));

            BufferedReader stdError = new BufferedReader(new 
                                                         InputStreamReader(p.getErrorStream()));

            // read the output from the command
            //System.out.println("Here is the standard output of the command:\n");
            while ((s = stdInput.readLine()) != null) {
                //System.out.println(s);
                sb.append(s).append("\n");
            }
            
            // read any errors from the attempted command
            //System.out.println("Here is the standard error of the command (if any):\n");
            while ((s = stdError.readLine()) != null) {
                System.out.println(s);
            }
            
            //System.exit(0);
        }
        catch (IOException e) {
            System.out.println("exception happened - here's what I know: ");
            e.printStackTrace();
            System.exit(-1);
        }
        
        return sb.toString();
    }
    //READS IN THE FILE AND STORE THEM TO sm AS [sub, tag]
    public static void readMapFile(String file, HashMap<String, String> sm) {

        String str = "";
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(file));
                while ((str = txtin.readLine()) != null) {
                    //DOCTOR,NAME
                    //sub, tag
                    String s[] = str.split(",");
                    String sub = s[0];
                    String tag = s[1];
                    sm.put(sub, tag);
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
        
    //EXECUTE TRAIN AND TEST
    //args FOR REFERENCE DIR AND TEXT DIR
    public static void exec(String[] args, boolean ifTrain, String year,
                            HashMap<String, HashMap<String, Double>> dps,
                            HashMap<String, String> sm, double th, boolean ifWeight) {

        // add input systems
        ArrayList<String> inDirs = new ArrayList<String>();
        addDir(inDirs, args);
        
        // list text files
        ArrayList<String> fileList = new ArrayList<String>();
        String txtDir = args[1];        
        listFile(txtDir, fileList);

        HashSet<String> refs = new HashSet<String>();
        if (ifTrain) {
            String refDir = args[0];       
            // read ref. concepts
            for (String fileName : fileList) {
                getCons(refDir, fileName, refs);
            }
        }

        ArrayList<HashSet<String>> instList = new ArrayList<HashSet<String>>();
        setConMap(inDirs, fileList, instList);
        
        if (ifTrain) {
            train(instList, refs, dps, sm, ifWeight);
        } else {
            String outDir = args[2];
            File oDir = new File(outDir);
            if (oDir.exists()) {
                
                File[] files = oDir.listFiles();
                if(files != null) { //some JVMs return null for empty dirs
                    for(File f: files) {
                        f.delete();
                    }
                }                
                oDir.delete();
                if (oDir.exists()) {
                    System.out.println("dir not delete");
                }
            }
            oDir.mkdir();
        
            test(instList, dps, sm, txtDir, outDir, year, th);
        }

    }        
    //TRAINING
    //instList is a list of sets of "fileName + " " + start + " " + end + " " + type1" from inDirs
    public static void train(ArrayList<HashSet<String>> instList, HashSet<String> refs, 
                             HashMap<String, HashMap<String, Double>> dps,
                             HashMap<String, String> sm, boolean ifWeight) {
        
        // collect span info of reference concepts
        HashSet<String> rSpan = new HashSet<>();
        for (String ref : refs) {            
            String r[] = ref.split(" ");
            String rf = r[0];
            int rB = Integer.parseInt(r[1]);
            int rE = Integer.parseInt(r[2]);
            rSpan.add(rf + " " + rB + " " + rE);
        }        
        //cnts FOR COUNTING TYPES
        HashMap<String, Double> cnts = new HashMap<>();
        
        // collect system outputs for false concepts
        HashSet<String> nones = new HashSet<>();
        for (int i = 0; i < instList.size(); i++) {
            HashSet<String> anss = instList.get(i);
            for (String ans : anss) {                
                String r[] = ans.split(" ");
                String rf = r[0];
                int rB = Integer.parseInt(r[1]);
                int rE = Integer.parseInt(r[2]);
                
                // skip if matched with reference span
                if (rSpan.contains(rf + " " + rB + " " + rE)) {
                    continue;
                }
                // add as negative examples
                ans = rf + " " + rB + " " + rE + " " + "NONE";
                if (!nones.contains(ans)) {
                    nones.add(ans);
                }
            }
        }
        // counts for negative examples
        cnts.put("NONE", nones.size() * 1.0);                    
        
        refs.addAll(nones);
        
        for (String ref : refs) {            
            String r[] = ref.split(" ");
            //fileName + " " + start + " " + end + " " + type1; // fileName added
            String rf = r[0];
            int rB = Integer.parseInt(r[1]);
            int rE = Integer.parseInt(r[2]);
            String rS = r[3];
            //cnts counts the occurence of different type1s
            // check count for only positive except negatives
            if (!rS.equalsIgnoreCase("NONE")) {
                if (!cnts.containsKey(rS)) {
                    cnts.put(rS, 1.0);
                } else {
                    double c = cnts.get(rS) + 1;
                    cnts.put(rS, c);                
                }
            }
            
            // compare to get match span exact
            // exact sub, exact type
            //ADD TO dp
            HashSet<String> dp = new HashSet<>();
            for (int i = 0; i < instList.size(); i++) {
                HashSet<String> anss = instList.get(i);
                for (String ans : anss) {
                    String a[] = ans.split(" ");
                    String af = a[0];
                    if (!rf.equals(af)) {
                        continue;
                    }
                    int aB = Integer.parseInt(a[1]);
                    int aE = Integer.parseInt(a[2]);
                    //aS-type
                    String aS = a[3];                    
                    //aT-super type
                    String aT = sm.get(aS);
                            
                    if (rB == aB && rE == aE) {
                        dp.add(i + " es " + aS);
                        dp.add(i + " et " + aT);                       
                        //System.out.println(i + " " + aS);            
                    }
                    /*
                      if (!(rE <= aB || aE <= rB)) { // partial
                      dp.add(i + " ps " + aS);
                      dp.add(i + " pt " + aT);                                               
                      }
                    */
                }                
            }
            
            if (!dps.containsKey(rS)) {
                HashMap<String, Double> v = new HashMap<>();
                for (String d : dp) {
                    // give more weight to high performance one
                    double w = 1.0;
                    if (ifWeight) {
                        w = Double.parseDouble(d.split(" ", 2)[0]) + 1;
                    }
                    v.put(d, 1.0 / w);
                }
                dps.put(rS, v);
            } else {
                HashMap<String, Double> v = dps.get(rS);
                for (String d : dp) {
                    // give more weight to high performance one
                    double w = 1.0;
                    if (ifWeight) {
                        w = Double.parseDouble(d.split(" ", 2)[0]) + 1;
                    }                    
                    if (v.containsKey(d)) {
                        double dv = v.get(d) + 1 / w;
                        v.put(d, dv);
                    } else {
                        v.put(d, 1.0 / w);                       
                    }
                }
            }
        }
                
        for (String t : dps.keySet()) {
            //c-global frequency
            double c = cnts.get(t);
            HashMap<String, Double> v = dps.get(t);
            for (String d : v.keySet()) {
                double dv = v.get(d) / c;
                v.put(d, dv);
            }            
        }
        
        /*
          for (String t : dps.keySet()) {
          System.out.println(t);
          HashMap<String, Double> v = dps.get(t);
          for (String d : v.keySet()) {
          System.out.println("\t" + d + "\t" + v.get(d));
          }                        
          }
        */
    }
    
    public static void test(ArrayList<HashSet<String>> instList, HashMap<String, HashMap<String, Double>> dps,
                            HashMap<String, String> sm, String txtDir,
                            String outDir, String year, double th) {

        // collect system outputs
        HashMap<String, Integer> orders = new HashMap<>();
        for (int i = 0; i < instList.size(); i++) {
            HashSet<String> anss = instList.get(i);
            for (String ans : anss) {                
                if (!orders.containsKey(ans)) {
                    orders.put(ans, i);
                }
            }
        }
        
        // collect classifiers output information
        HashMap<String, TreeMap<String, String>> conCand = new HashMap<String, TreeMap<String, String>>();
        HashMap<String, TreeMap<String, Integer>> conOrder = new HashMap<String, TreeMap<String, Integer>>();
        HashMap<String, TreeMap<String, Double>> conScore = new HashMap<String, TreeMap<String, Double>>();
        
        HashSet<String> done = new HashSet<>();
        
        for (String ref : orders.keySet()) {            
            String r[] = ref.split(" ");
            //fileName + " " + start + " " + end + " " + type1; // fileName added
            //rf-fileName
            String rf = r[0];
            //rB-start
            int rB = Integer.parseInt(r[1]);
            //rE-end
            int rE = Integer.parseInt(r[2]);

            if (done.contains(rf + " " + rB + " " + rE)) {
                continue;
            }    
            //order - index
            int order = orders.get(ref);
            //rS-type1
            String rS = r[3];
            
            HashSet<String> dp = new HashSet<>();
            for (int i = 0; i < instList.size(); i++) {
                HashSet<String> anss = instList.get(i);
                for (String ans : anss) {
                    String a[] = ans.split(" ");
                    String af = a[0];
                    if (!rf.equals(af)) {
                        continue;
                    }                    
                    int aB = Integer.parseInt(a[1]);
                    int aE = Integer.parseInt(a[2]);
                    String aS = a[3];                    
                    String aT = sm.get(aS);
                            
                    if (rB == aB && rE == aE) {
                        dp.add(i + " es " + aS);
                        dp.add(i + " et " + aT);
                        //System.out.println(i + " " + aS);         
                    }
                    /*
                      if (!(rE <= aB || aE <= rB)) { // partial
                      dp.add(i + " ps " + aS);
                      dp.add(i + " pt " + aT);                                               
                      }
                    */
                }                
            }
            
            String mc = "";
            double max = -1;
            for (String c : dps.keySet()) {
                double sim = cosine(dp, dps.get(c));
                //System.out.println(c + " " + sim);      
                if (sim > max) {
                    max = sim;
                    mc = c;
                }                        
            }
            //System.out.println(gS + "\t" + mc + "\t" + max);
            
            if (max > th && !mc.equalsIgnoreCase("NONE")) { //0.7
                // get type for target data
                String tag = sm.get(mc);
                //System.out.println(gS + "\t" + mc + "\t" + max);
                // set new key
                String nKey = rB + " " + rE + " " + rS;
                String outStr = "<" + tag + " id=\"P0\" start=\"" + rB + "\" end=\"" + rE + "\" TYPE=\"" + mc + "\" text=\"\" />";
                //System.out.println(outStr);
                
                if (!conCand.containsKey(rf)) {
                    TreeMap<String, String> tMap = new TreeMap<String, String>();
                    tMap.put(nKey, outStr);
                    conCand.put(rf, tMap);
                    
                    TreeMap<String, Integer> toMap = new TreeMap<String, Integer>();
                    toMap.put(nKey, order);
                    conOrder.put(rf, toMap);
                    
                    TreeMap<String, Double> tsMap = new TreeMap<String, Double>();
                    tsMap.put(nKey, max);
                    conScore.put(rf, tsMap);                   
                    
                } else {
                    conCand.get(rf).put(nKey, outStr);
                    conOrder.get(rf).put(nKey, order);
                    conScore.get(rf).put(nKey, max);
                }
            }
            done.add(rf + " " + rB + " " + rE);
            
        }
        
        for (String f : conCand.keySet()) {
            //output
            ArrayList<String> inst = new ArrayList<String>();
            
            TreeMap<String, String> tMap = conCand.get(f);
            TreeMap<String, Integer> toMap = conOrder.get(f);
            TreeMap<String, Double> tsMap = conScore.get(f);            
            
            overlap(tMap, toMap, tsMap, inst);                    
            writeListFile(f, inst, txtDir, outDir, year);
        }        
    }        
    
    public static void addDir(ArrayList<String> inDirs, String[] args) {
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
    }
    
    public static void setConMap(ArrayList<String> inDirs,  ArrayList<String> fileList, ArrayList<HashSet<String>> instList) {
        for (String inDir : inDirs) {
            HashSet<String> anss = new HashSet<String>();
            for (String fileName : fileList) {
                getCons(inDir, fileName, anss);
            }
            instList.add(anss);
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
                               TreeMap<String, Integer> orders,
                               TreeMap<String, Double> scores,
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
                double score = scores.get(key);
                boolean ifMost = true;
                for (String key3: overs.keySet()) {
                    double score3 = scores.get(key3);
                    
                    if (score < score3) {
                        ifMost = false;
                    } else if (score == score3) {
                        oSet.add(key3);
                        System.out.println("same score: " + score + " " + key + "  |  " + key3);
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
                        int order = orders.get(key);
                        
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

    public static void getCons(String inDir, String fileName, HashSet<String> set) {
    
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
        if (document.getElementsByTag("NGRID_deId").first() != null) {
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
                String key = fileName + " " + start + " " + end + " " + type1; // fileName added
                if (!set.contains(key)) {
                    set.add(key);
                }
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

    public static void writeListFile(String name, ArrayList<String> outs, String txtDir, String outDir, String year) {

        //System.out.println(name + " " + outs.size());
        
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
    
    public static double cosine(HashSet<String> l, HashMap<String, Double> g) {
        double dotProduct = 0.0;
        double normA = l.size();
        double normB = 0.0;
        for (String c : g.keySet()) {
            if (l.contains(c)) {
                dotProduct += g.get(c);
            }
            normB += Math.pow(g.get(c), 2);                
        }   
        return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
    }
}
