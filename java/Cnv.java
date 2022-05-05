/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

import java.io.*;
import java.util.ArrayList;
import java.util.HashMap;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

/**
 *
 * @author jun
 */
public class Cnv {

    
    public static void main(String[] args) {

        String smFile = "data/i2b2/i2b2_2014_type.txt";
        HashMap<String, String> sm = new HashMap<String, String>();
        readMatchMap(sm, smFile);                
        
        String mapDir = "data/i2b2/i2b2_deid/map/";
        
        String cs[] = {"04", "06", "14", "16"}; 
        String years[] = {"2014", "2014", "2014", "2016"};        

        for (int i = 0; i < cs.length; i++) {
            for (int j = 0; j < cs.length; j++) {
                if (i == j) {
                    continue;
                }
                String cM = cs[i]; // model
                String cT = cs[j]; // test data
                String sYear = years[i];
                String dYear = years[j];
                
                String tA[] = {"train", "test"};
                
                for (String tt : tA) {
                    String srcDir = "data/i2b2/20" + cT + "deid/" + tt + "/con_rnnE_" + cM + "_" + cT + "_ne_nf/";
                    String dstDir = "data/i2b2/20" + cT + "deid/" + tt + "/con_rnnE_" + cM + "_" + cT + "_ne/";

                    File dst = new File(dstDir);
                    if (!dst.exists()) {
                        dst.mkdirs();
                    }
                    String mapFile = mapDir + cM + "_" + cT + ".txt";
                    HashMap<String, String> cnvM = new HashMap<>();
                    readMap(mapFile, cnvM);

                    ArrayList<String> fileList = new ArrayList<String>();
                    // list dir
                    listFile(srcDir, fileList);

                    //System.out.println("ans: " + cM + " ref: " + cM + " year: " + yA + " " + yR);
                    for (int k = 0; k < fileList.size(); k++) {
                        String fileName = fileList.get(k);
                        readFile(srcDir, fileName, dstDir, cnvM, sm, sYear, dYear);
                    } // each file                    
                } // tr or ts
            }   // data     
        } // model

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
    
     public static void readMatchMap(HashMap<String, String> map, String file) {

        String str = "";
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(file));

                while ((str = txtin.readLine()) != null) {
                    String sA[] = str.split(",");
                    map.put(sA[0].trim(), sA[1].trim());
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
    
    public static void readMap(String file, HashMap<String, String> map) {
    
        String str;
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(file));

                while ((str = txtin.readLine()) != null) {
                    String s[] = str.split("\t", 2);
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
    
    public static void readFile(String srcDir, String file, String dstDir, HashMap<String, String> cnvM,
            HashMap<String, String> sm, String sYear, String dYear) {
    
        String strA;
        StringBuilder sb = new StringBuilder();
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(srcDir + file));

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
        if (sYear.equals("2016")) {
            //System.out.println("2016");            
            deIdi2b2 = document.getElementsByTag("NGRID_deId").first();     
        } else {
            deIdi2b2 = document.getElementsByTag("deIdi2b2").first();                 
        }
        
        Element tags = deIdi2b2.getElementsByTag("TAGS").first();
        
        ArrayList<String> outs = new ArrayList<String>();
        
        if (tags == null) {
            System.out.println("null");
        } else {
            Elements ts = tags.children();
            for (Element t : ts) {
                String id = t.attr("id");
                String start = t.attr("start");
                String end = t.attr("end");
                String text = t.attr("text");
                String type1 = t.attr("type");
                //String cType = t.tagName();       
                
                String nT = "";
                String nC = "";                
                if (cnvM.containsKey(type1)) {
                    nT = cnvM.get(type1);
                    nC = sm.get(nT);
                    
                    //<LOCATION id="P0" start="22" end="29" text="CALVERT" TYPE="HOSPITAL" comment="" />
                    outs.add("<" + nC + " id=\"" + id + "\" start=\"" + start + "\" end=\"" 
                        + end + "\" text=\"" + text + "\" TYPE=\"" + nT + "\" comment=\"\" />");
                } else {
                    //System.out.println("no cnv mapping: " + type1);
                    //System.out.println(srcDir + " " + dstDir);
                }
                
            }
        }
        
        
        ArrayList<String> txts = new ArrayList<String>();
        readTxtFile(srcDir + file, txts);
                        
        writeListXml(dstDir + file, outs, txts, dYear);
    }
        
    public static PrintWriter getPrintWriter (String file)
    throws IOException {
        return new PrintWriter (new BufferedWriter
                (new FileWriter(file)));
    }
    
    public static void writeListXml(String file, ArrayList<String> outs, ArrayList<String> txts, String year) {

        try {
            PrintWriter out = getPrintWriter(file);
            
            for (String t : txts) {
                if (t.trim().equalsIgnoreCase("<deIdi2b2>") && year.equalsIgnoreCase("2016")) {
                    out.println("<NGRID_deId>");                        
                } else if (t.trim().equalsIgnoreCase("<NGRID_deId>") && year.equalsIgnoreCase("2014")) {
                    out.println("<deIdi2b2>");                        
                } else {
                    out.println(t);
                }                
            }
            out.println("<TAGS>");
            for (String t : outs) {
                out.println(t);
            }
            if (year.equals("2014")) {
                out.println("</TAGS>\n</deIdi2b2>");
            } else if (year.equals("2016")) {
                out.println("</TAGS>\n</NGRID_deId>");                
            } else {
                out.println("</TAGS>\n</NGRID_deId>");                                
            }
            out.flush();
            out.close();
        } catch (IOException e) {
            e.printStackTrace ();
        }
        //System.out.println(idx.size());
    }
}
