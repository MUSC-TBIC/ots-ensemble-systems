/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */


import java.io.*;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.TreeMap;
import java.util.TreeSet;
import java.util.logging.Level;
import java.util.logging.Logger;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Document.OutputSettings;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

/**
 *
 * @author jun
 */
public class StackDeidNE {

    /**
     * @param args the command line arguments
     */

    static boolean ifFirst = true;
        
    public static void main(String[] args) {
                
        String txtDir = args[0];
        String outFile = args[1];
        String outFileL = args[2];
        
        String cFile = args[3];
        String tFile = args[4];
        
        String refDir = args[5];
        
        HashMap<String, Integer> classMap = new HashMap<>();
        readClassfile(cFile, classMap);    
        
        HashMap<String, Integer> tagMap = new HashMap<>();
        HashMap<String, String> typeMap = new HashMap<>();
        readTypefile(tFile, typeMap, tagMap);    
        
        // add input systems
        ArrayList<String> inDirs = new ArrayList<String>();
        
        for (int i = 6; i < args.length; i++) {
            if (args[i] == null || args[i].trim().isEmpty()) {
                continue;
            }
            inDirs.add(args[i]);
        }
        
        // list text files
        ArrayList<String> fileList = new ArrayList<String>();
        listFile(txtDir, fileList);
        
        ArrayList<String> outs = new ArrayList<String>();
        ArrayList<String> outsL = new ArrayList<String>();
        
        for (int i= 0; i < fileList.size(); i++) {
            String fileName = fileList.get(i).replace(".txt", ".xml");
            
            //read ref
            TreeMap<String, String> refMap = new TreeMap<String, String>();
            getRefs(refDir, fileName, refMap);
                        
            ArrayList<TreeMap<String, String>> instList = new ArrayList<TreeMap<String, String>>();
            
            for (String inDir : inDirs) {
                TreeMap<String, String> instMap = new TreeMap<String, String>();
                getCons(inDir, fileName, instMap);
                instList.add(instMap);
            }
            
            TreeMap<String, String> maps = new TreeMap<String, String>();
            // se cp match
            // sp cp match
            TreeMap<String, TreeSet<Integer>> secpCnts = new TreeMap<String, TreeSet<Integer>>();
            TreeMap<String, TreeSet<Integer>> spcpCnts = new TreeMap<String, TreeSet<Integer>>();
            TreeMap<String, TreeSet<Integer>> rmCnts = new TreeMap<String, TreeSet<Integer>>();
            TreeMap<String, TreeSet<Integer>> lmCnts = new TreeMap<String, TreeSet<Integer>>();
            TreeMap<String, TreeSet<Integer>> inCnts = new TreeMap<String, TreeSet<Integer>>();
            TreeMap<String, TreeSet<Integer>> outCnts = new TreeMap<String, TreeSet<Integer>>();
            
            TreeMap<String, TreeSet<Integer>> eIdxs = new TreeMap<String, TreeSet<Integer>>();
            TreeMap<String, TreeMap<Integer, String>> pIdxs = new TreeMap<String, TreeMap<Integer, String>>();

            TreeMap<String, Integer> lEmaps = new TreeMap<String, Integer>();
            
            HashMap<String, TreeMap<Integer, String>> typeM = new HashMap<>();            
            HashMap<String, TreeMap<Integer, String>> tagM = new HashMap<>();            
            
            collect(instList, maps, secpCnts, spcpCnts, 
                    eIdxs, pIdxs, rmCnts, lmCnts, inCnts, outCnts, typeM, tagM, typeMap);            
            // map key chaged to type to tag
            makeLabel(refMap, lEmaps, maps, classMap);
            
            makeInst(lEmaps, maps, secpCnts, spcpCnts, eIdxs,
                    pIdxs, rmCnts, lmCnts, inCnts, outCnts,
                    outs, outsL, fileName, instList.size(), classMap, tagMap, typeM, tagM);
            
            if (i % 20 == 0 && i != 0 ) {
                System.out.println(i);
            } else {
                System.out.print(i + "\t");
            }
        }
        // 1 yes
        // 0 no
        
        System.out.println("");
        writeListFile(outFile, outs);
        writeListFile(outFileL, outsL);
        
    }
    
    public static void makeInst(TreeMap<String, Integer> lmaps, 
        TreeMap<String, String> maps,
        TreeMap<String, TreeSet<Integer>> secpCnts,
        TreeMap<String, TreeSet<Integer>> spcpCnts,
        TreeMap<String, TreeSet<Integer>> eIdxs,
        TreeMap<String, TreeMap<Integer, String>> pIdxs,
        TreeMap<String, TreeSet<Integer>> rmCnts, 
        TreeMap<String, TreeSet<Integer>> lmCnts, 
        TreeMap<String, TreeSet<Integer>> inCnts, 
        TreeMap<String, TreeSet<Integer>> outCnts,
        ArrayList<String> outs,
        ArrayList<String> outsL, String fileName,
        int mSize, HashMap<String, Integer> classMap, HashMap<String, Integer> tagMap, 
        HashMap<String, TreeMap<Integer, String>> typeMG,
        HashMap<String, TreeMap<Integer, String>> tagMG) {
    
        for (String key :  maps.keySet()) {

            int label = lmaps.get(key);
            
            int eSize = 40;
            
            // get text count start
            String keyA[] = key.split(" ");
            int s1 = Integer.parseInt(keyA[0]);
            int e1 = Integer.parseInt(keyA[1]);
            
            int idx = 1;
            StringBuilder sb = new StringBuilder();
            //1 1:1.0 11:1.0 11:1.0 12:1.0 13:1.0 14:1.0 15:1.0 16:1.0 17:1.0 18:1.0 
            
            if (ifFirst) {
                System.out.println("secpCnts");
                System.out.println(idx);
            }
            idx = appendB(secpCnts, key, idx, sb);
            
            if (ifFirst) {
                System.out.println("spcpCnts");
                System.out.println(idx);
            }
            idx = appendB(spcpCnts, key, idx, sb);

            if (ifFirst) {
                System.out.println("rmCnts");
                System.out.println(idx);
            }
            idx = appendB(rmCnts, key, idx, sb);
            
            if (ifFirst) {
                System.out.println("lmCnts");
                System.out.println(idx);
            }
            idx = appendB(lmCnts, key, idx, sb);
            
            if (ifFirst) {
                System.out.println("inCnts");
                System.out.println(idx);
            }
            idx = appendB(inCnts, key, idx, sb);

            if (ifFirst) {
                System.out.println("outCnts");
                System.out.println(idx);
            }
            idx = appendB(outCnts, key, idx, sb);
            
            if (ifFirst) {
                System.out.println("secpCnts");
                System.out.println(idx);
            }
            if (secpCnts.containsKey(key)) {
                TreeSet<Integer> tE = secpCnts.get(key);
                int size = tE.size();
                idx = appendN(sb, size, eSize, idx); // number of matches
                idx = append(sb, tE, eSize, idx); // pair of matches
            } else {
                idx = idx + eSize;// number of matches
                idx = idx + eSize;// pair of matches
            }                 
            
            if (ifFirst) {
                System.out.println("spcpCnts");
                System.out.println(idx);
            }
            if (spcpCnts.containsKey(key)) {
                TreeSet<Integer> tE = spcpCnts.get(key);
                int size = tE.size();
                idx = appendN(sb, size, eSize, idx); // number of matches
                idx = append(sb, tE, eSize, idx); // pair of matches
            } else {
                idx = idx + eSize;// number of matches
                idx = idx + eSize;// pair of matches
            }           
            
            if (ifFirst) {
                System.out.println("rmCnts");
                System.out.println(idx);
            }
            if (rmCnts.containsKey(key)) {
                TreeSet<Integer> tE = rmCnts.get(key);
                int size = tE.size();
                idx = appendN(sb, size, eSize, idx); // number of matches
                idx = append(sb, tE, eSize, idx); // pair of matches
            } else {
                idx = idx + eSize;// number of matches
                idx = idx + eSize;// pair of matches
            }           
            
            if (ifFirst) {
                System.out.println("lmCnts");
                System.out.println(idx);
            }
            if (lmCnts.containsKey(key)) {
                TreeSet<Integer> tE = lmCnts.get(key);
                int size = tE.size();
                idx = appendN(sb, size, eSize, idx); // number of matches
                idx = append(sb, tE, eSize, idx); // pair of matches
            } else {
                idx = idx + eSize;// number of matches
                idx = idx + eSize;// pair of matches
            }           
            
            if (ifFirst) {
                System.out.println("inCnts");
                System.out.println(idx);
            }
            if (inCnts.containsKey(key)) {
                TreeSet<Integer> tE = inCnts.get(key);
                int size = tE.size();
                idx = appendN(sb, size, eSize, idx); // number of matches
                idx = append(sb, tE, eSize, idx); // pair of matches
            } else {
                idx = idx + eSize;// number of matches
                idx = idx + eSize;// pair of matches
            }           
            
            if (ifFirst) {
                System.out.println("outCnts");
                System.out.println(idx);
            }
            if (outCnts.containsKey(key)) {
                TreeSet<Integer> tE = outCnts.get(key);
                int size = tE.size();
                idx = appendN(sb, size, eSize, idx); // number of matches
                idx = append(sb, tE, eSize, idx); // pair of matches
            } else {
                idx = idx + eSize;// number of matches
                idx = idx + eSize;// pair of matches
            }           
            
            if (ifFirst) {
                System.out.println("pIdxs");
                System.out.println(idx);
            }
            if (pIdxs.containsKey(key)) {
                TreeMap<Integer, String> tE = pIdxs.get(key);
                idx = append(sb, tE, eSize, idx); // pair of matches
            } else {
                idx = idx + eSize;// number of matches
            }
            
            if (ifFirst) {
                System.out.println("classMap");
                System.out.println(idx);
            }

            //idx i classMap
            //idx, mSize, classMap.size

            //System.out.println("*********");
            TreeMap<Integer, String> typeM = typeMG.get(key);
            for (int k = 0; k < mSize; k++) {
                if (typeM != null && typeM.containsKey(k)) {
                    int cI = classMap.get(typeM.get(k).toUpperCase());
                    sb.append(idx + cI).append(":1.0 ");
                    //System.out.println(k + " " + tF.get(k).toUpperCase() + " " + cI);
                }
                idx += classMap.size() + 1;
            }            
            
            TreeMap<Integer, String> tagM = tagMG.get(key);
            for (int k = 0; k < mSize; k++) {
                if (tagM != null && tagM.containsKey(k)) {
                    int cI = tagMap.get(tagM.get(k).toUpperCase());
                    sb.append(idx + cI).append(":1.0 ");
                    //System.out.println(k + " " + tF.get(k).toUpperCase() + " " + cI);
                }
                idx += tagMap.size() + 1;
            }            
            //System.out.println("*********");
            
            if (ifFirst) {
                System.out.println("end");
                System.out.println(idx);
            }
            
            String cType = "NONE";
            
            outs.add(label + " " + sb.toString());
            String outStr = fileName + " " + s1 + " " + e1 + " " + cType + " " + cType;
            outsL.add(outStr);
            
            if (ifFirst) {
                ifFirst = false;
            }
        }
    
    }
    
    public static int appendB(TreeMap<String, TreeSet<Integer>> map, String key, int idx, StringBuilder sb) { 
        if (map.containsKey(key)) {
            sb.append(idx++).append(":1.0 ");
            idx++;
        } else {
            idx++;
            sb.append(idx++).append(":1.0 ");
        }
        return idx;
    }

    public static int appendN(StringBuilder sb, int size, int len, int start){
        for (int i = 1; i < len; i++) {
            if (i <= size) {
                sb.append(start + i).append(":1.0 ");
            }
        }
	return start + len;
    }

    public static int append(StringBuilder sb, int i, int len, int start){
        sb.append(start + i).append(":1.0 ");
	return start + len;
    }

    public static int append(StringBuilder sb, TreeSet<Integer> set, int len, int start){
        
        for (int i : set) {
            sb.append(start + i).append(":1.0 ");
        }
	return start + len;
    }
    
    public static int append(StringBuilder sb, TreeMap<Integer, String> map, int len, int start){
        
        for (int i : map.keySet()) {
            sb.append(start + i).append(":1.0 ");
        }
	return start + len;
    }
    
    public static void makeLabel(TreeMap<String, String> refMap,
        TreeMap<String, Integer> lEmaps, // label exaxt => each class
        TreeMap<String, String> maps, HashMap<String, Integer> classMap) {
    
        for (String key1 : maps.keySet()) {
                        
            String type1 = "NONE";            
            if (refMap.containsKey(key1)) {
                type1 = refMap.get(key1).toUpperCase();
            } 
            int lbl = classMap.get(type1);
            lEmaps.put(key1, lbl);
        }
    
    }
                    
    public static void collect(ArrayList<TreeMap<String, String>> instList,
        TreeMap<String, String> maps,
        TreeMap<String, TreeSet<Integer>> secpCnts,
        TreeMap<String, TreeSet<Integer>> spcpCnts,
        TreeMap<String, TreeSet<Integer>> eIdxs,
        TreeMap<String, TreeMap<Integer, String>> pIdxs,
        TreeMap<String, TreeSet<Integer>> rmCnts, 
        TreeMap<String, TreeSet<Integer>> lmCnts, 
        TreeMap<String, TreeSet<Integer>> inCnts, 
        TreeMap<String, TreeSet<Integer>> outCnts,   
        HashMap<String, TreeMap<Integer, String>> typeM,
        HashMap<String, TreeMap<Integer, String>> tagM,
        HashMap<String, String> typeMap) {
        
        for (int i = 0; i < instList.size(); i++) { //each component
            TreeMap<String, String> map1 = instList.get(i);
        
            for (String key1: map1.keySet()) {
                
                //start + " " + end
                String keyA1[] = key1.split(" ");
                String cType1 = map1.get(key1);
                String tag1 = typeMap.get(cType1);
                
                if (!typeM.containsKey(key1)) {
                    TreeMap<Integer, String> tF = new TreeMap<>();
                    tF.put(i, cType1);
                    typeM.put(key1, tF);
                } else {
                    typeM.get(key1).put(i, cType1);
                }
                if (!tagM.containsKey(key1)) {
                    TreeMap<Integer, String> tF = new TreeMap<>();
                    tF.put(i, tag1);
                    tagM.put(key1, tF);
                } else {
                    tagM.get(key1).put(i, tag1);
                }
                
                if (!eIdxs.containsKey(key1)) {
                    TreeSet<Integer> eIdx = new TreeSet<Integer>();
                    eIdx.add(i);
                    eIdxs.put(key1, eIdx);
                } else if (!eIdxs.get(key1).contains(i)) {
                    eIdxs.get(key1).add(i);
                }

                if (!pIdxs.containsKey(key1)) {
                    TreeMap<Integer, String> pIdx = new TreeMap<Integer, String>();
                    pIdx.put(i, key1);
                    pIdxs.put(key1, pIdx);
                } else if (!pIdxs.get(key1).containsKey(i)) {
                    pIdxs.get(key1).put(i, key1);
                }
                
                int s1 = Integer.parseInt(keyA1[0]);
                int e1 = Integer.parseInt(keyA1[1]);
            
                TreeSet<Integer> rs = new TreeSet<Integer>();
                for (int j = s1; j < e1; j++) {
                    rs.add(j);
                }
                
                for (int j = 0; j < instList.size(); j++) { // each component
                
                    if (i == j) {
                        continue;
                    }
                    
                    TreeMap<String, String> map2 = instList.get(j);

                    for (String key2 : map2.keySet()) {
                        
                        String keyA2[] = key2.split(" ");
                        
                        int s2 = Integer.parseInt(keyA2[0]);
                        int e2 = Integer.parseInt(keyA2[1]);

                        if (s1 == s2 && e1 == e2) {
                            if (!secpCnts.containsKey(key1)) {
                                TreeSet<Integer> tE = new TreeSet<Integer>();
                                tE.add(i);
                                tE.add(j);
                                secpCnts.put(key1, tE);
                            } else if (!secpCnts.get(key1).contains(i)) {
                                TreeSet<Integer> tE = secpCnts.get(key1);
                                tE.add(i);
                            } else if (!secpCnts.get(key1).contains(j)) {
                                TreeSet<Integer> tE = secpCnts.get(key1);
                                tE.add(j);
                            }
                        }
                        
                        if (e1 == e2) {
                            if (!rmCnts.containsKey(key1)) {
                                TreeSet<Integer> tE = new TreeSet<Integer>();
                                tE.add(j);
                                rmCnts.put(key1, tE);
                            } else if (!rmCnts.get(key1).contains(j)) {
                                TreeSet<Integer> tE = rmCnts.get(key1);
                                tE.add(j);
                            }
                        }
                        if (s1 == s2) {
                            if (!lmCnts.containsKey(key1)) {
                                TreeSet<Integer> tE = new TreeSet<Integer>();
                                tE.add(j);
                                lmCnts.put(key1, tE);
                            } else if (!lmCnts.get(key1).contains(j)) {
                                TreeSet<Integer> tE = lmCnts.get(key1);
                                tE.add(j);
                            }
                        }
                        if (s1 < s2 && e2 < e1) {
                            if (!inCnts.containsKey(key1)) {
                                TreeSet<Integer> tE = new TreeSet<Integer>();
                                tE.add(j);
                                inCnts.put(key1, tE);
                            } else if (!inCnts.get(key1).contains(j)) {
                                TreeSet<Integer> tE = inCnts.get(key1);
                                tE.add(j);
                            }
                        }
                        if (s2 < s1 && e1 < e2) {
                            if (!outCnts.containsKey(key1)) {
                                TreeSet<Integer> tE = new TreeSet<Integer>();
                                tE.add(j);
                                outCnts.put(key1, tE);
                            } else if (!outCnts.get(key1).contains(j)) {
                                TreeSet<Integer> tE = outCnts.get(key1);
                                tE.add(j);
                            }
                        }
                        
                        boolean ifPart = false;
                        for (int k = s2 ; k < e2 ; k++) {
                            if (rs.contains(k)) {
                                ifPart = true;
                                break;
                            }
                        } 
                        
                        if (ifPart) {                            
                            // missing in original Stack4, need to revise 
                            if (!pIdxs.get(key1).containsKey(j)) {
                                pIdxs.get(key1).put(j, key2);
                            }
                            
                            if (!spcpCnts.containsKey(key1)) {
                                TreeSet<Integer> tE = new TreeSet<Integer>();
                                tE.add(i);
                                tE.add(j);
                                spcpCnts.put(key1, tE);
                            } else if (!spcpCnts.get(key1).contains(i)) {
                                TreeSet<Integer> tE = spcpCnts.get(key1);
                                tE.add(i);
                            } else if (!spcpCnts.get(key1).contains(j)) {
                                TreeSet<Integer> tE = spcpCnts.get(key1);
                                tE.add(j);
                            }

                        }
                    } // for key2
                } // for each instList inner
            
                if (!maps.containsKey(key1)) {
                    maps.put(key1, map1.get(key1));
                }
                
            } // for key1
            
        } // for each instList outer
        
    }
    
    public static void listFile(String dirName, ArrayList<String> fileList) {
        File dir = new File(dirName);

        String[] children = dir.list();
        if (children != null) {
            for (String filename : children) {
                if (filename.endsWith(".txt")) {
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
                txtin = new BufferedReader(new FileReader(inDir + fileName));

                while ((str = txtin.readLine()) != null) {
                    sb.append(str).append("\n");
                }
            } catch (Exception ex) {
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
                //String cType = t.tagName().toUpperCase();               
                //<DATE id="P0" start="16" end="26" text="2069-04-07" TYPE="DATE" comment="" />
                //String outStr = "<" + cType + " id=\"P0\" start=\"" + start + "\" end=\"" + end + "\" TYPE=\"" + type1 + "\"" + " text=\"\" />";
                //String outStr = fileName + " " + start + " " + end + " " + type1 + " " + cType;

                map.put(start + " " + end, type1);
            }
        }
    }
    
    public static void getRefs(String inDir, String fileName, TreeMap<String, String> map) {
    
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
                //String cType = t.tagName().toUpperCase();               
                //<DATE id="P0" start="16" end="26" text="2069-04-07" TYPE="DATE" comment="" />
                //String outStr = "<" + cType + " id=\"P0\" start=\"" + start + "\" end=\"" + end + "\" TYPE=\"" + type1 + "\"" + " text=\"\" />";
                map.put(start + " " + end, type1);                
            }
        }
    }
    
    public static String getTxt(String dir, String fileName) {
        
        byte[] bFile = null;
        try {        
            bFile = Files.readAllBytes(new File(dir, fileName).toPath());
        } catch (IOException ex) {
            Logger.getLogger(StackDeidNE.class.getName()).log(Level.SEVERE, null, ex);
        }
        return new String(bFile);
    }
    
    public static void readClassfile(String fileName, HashMap<String, Integer> map) {

        String str = "";
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(fileName));
                while ((str = txtin.readLine()) != null) {
                    String s[] = str.split("," , 2);
                    map.put(s[0], Integer.parseInt(s[1]));
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
    
    public static void readTypefile(String fileName, HashMap<String, String> map, HashMap<String, Integer> tMap) {

        String str = "";
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(fileName));
                int i = 1;
                while ((str = txtin.readLine()) != null) {
                    String s[] = str.split("," , 2);
                    String tag = s[1];
                    map.put(s[0], tag);
                    
                    if (!tMap.containsKey(tag)) {
                        tMap.put(tag, i);
                        i++;
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

    public static void writeListFile(String name, ArrayList<String> outs) {

        try {

            PrintWriter out = getPrintWriter(name);
            for (String s : outs) {
                out.println(s);
            }
            out.flush();
            out.close();
        } catch (IOException e) {
            e.printStackTrace ();
        }
        //System.out.println(idx.size());
    }
}
