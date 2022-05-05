/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

import java.io.*;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

/**
 *
 * @author jun
 */
public class AddPredictionsVW {

    /**
     * @param args the command line arguments
     */

    public static void main(String[] args) {

        String dmA[] = {"train", "test"};
        String dataA[] = {"04", "06", "14", "16"};
                        
        for (String dm : dmA) {
            String dmS = "tr";            
            if (dm.equals("test")) {
                dmS = "ts";
            }

            for (String data : dataA) {
                String inFile = "data/i2b2/20" + data + "deid/fv_out/deid" + data + "_fv_" + dmS + "_f.txt";
                String outFile = "data/vowpal_wabbit/test/deid_stack_new/deid" + data + "_fv_" + dmS + "_f_st.txt";

                String dir = "data/i2b2/20" + data + "deid/" + dm + "/";      
                String pDirs[] = {"04", "06", "14", "16"};

                String txtDir = dir + "txt";
                HashSet<String> fList = new HashSet<>();
                listFile(txtDir, fList, "txt");

                ArrayList<String> heads = new ArrayList<String>();
                ArrayList<String> fnames = new ArrayList<String>();
                ArrayList<Integer> begins = new ArrayList<Integer>();
                ArrayList<Integer> ends = new ArrayList<Integer>();
                ArrayList<String> tails = new ArrayList<String>();
                readFv(inFile, heads, fnames, begins, ends, tails);

                ArrayList<String> augs = new ArrayList<String>();
                for (String fname : fnames) {
                    augs.add("");
                }

                for (String p : pDirs) {
                    String year = "2014";
                    if (p.equals("16")) {
                        year = "2016";
                    }
                
                    if (p.equals(data)) {
                        p = dir + "con_rnnE_" + p + "_" + data + "_ne" + "/";
                        
                    } else {
                        p = dir + "con_rnnE_" + p + "_" + data + "_ne_nf" + "/";                        
                    }

                    HashMap<String, HashMap<Integer, String>> sps = new HashMap<>();
                    // make map for type and span
                    for (String f : fList) {
                        readOuts(p, f, sps, year);
                    }

                    // add to augs
                    add(augs, fnames, begins, ends, sps);
                }        
                writeFile(outFile, heads, augs, tails);                     
            } //data
              
        }  //dm
 
    }
    
    public static void add(ArrayList<String> augs, ArrayList<String> fnames,
            ArrayList<Integer> begins, ArrayList<Integer> ends, 
            HashMap<String, HashMap<Integer, String>> sps) {
    
        
        for (int i = 0; i < fnames.size(); i++) {
            if (fnames.get(i).isEmpty()) {
                continue;
            }
            
            String out = augs.get(i);
            
            int b = begins.get(i);
            int e = ends.get(i);
            String fname = fnames.get(i);
            HashMap<Integer, String> sp = sps.get(fname);
          
            String con = "O";
            for (int j = b; j < e; j++) {
                if (sp.containsKey(j)) {
                    con = sp.get(j);
                    break;
                }
            }
            
            augs.set(i, out + "\t" + con);
        }    
    
    }
    
    public static void listFile(String dirName, HashSet<String> fileList, String ext) {
        File dir = new File(dirName);

        String[] children = dir.list();
        if (children == null) {
            return;
        } else {
            for (int i = 0; i < children.length; i++) {
                // Get filename
                String filename = children[i];
                if (filename.endsWith("." + ext)) {
                    fileList.add(filename);
                }
            }
        }

    }
    
    public static void readOuts(String dir, String fname, HashMap<String, HashMap<Integer, String>> sps,
        String year) {
    
        HashMap<Integer, String> sp = new HashMap<>();
        sps.put(fname, sp);
        
        File fe = new File (dir, fname.replace(".txt", ".xml"));
        if (!fe.exists()) {
            return;
        }
                        
        String strA;
        StringBuilder sb = new StringBuilder();
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(dir + fname.replace(".txt", ".xml")));

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
                int b = Integer.parseInt(t.attr("start"));
                int e = Integer.parseInt(t.attr("end"));
                String type1 = t.attr("type").toUpperCase();
                //String cType = t.tagName().toUpperCase();               
                
                HashMap<Integer, String> tmp = sps.get(fname);
                for (int i = b ; i < e; i++) {
                    if (i == b) {
                        tmp.put(i, "B-" + type1);
                    } else {
                        tmp.put(i, "I-" + type1);                            
                    }
                }                        
            }
        }
        
    }
    
    public static void readFv(String fileName, ArrayList<String> heads, ArrayList<String> fnames,
            ArrayList<Integer> begins, ArrayList<Integer> ends, ArrayList<String> tails) {

        String str = "";
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(fileName));

                while ((str = txtin.readLine()) != null) {
                    //13971	13973	13	175	100035.txt	O
                    //-6         -5   
                    
                    if (str.trim().isEmpty()) {
                        heads.add("");
                        fnames.add("");
                        begins.add(-1);
                        ends.add(-1);
                        tails.add("");
                    } else {
                        String s[] = str.split("\t");
                        int b = Integer.parseInt(s[s.length - 6]);
                        int e = Integer.parseInt(s[s.length - 5]);
                        
                        String hS = s[0].replace("|", "[-b-]").replace(":", "[-c-]").replace(" ", "[-s-]");
                        String tS = "";
                        for (int i = s.length - 6; i < s.length; i++) {
                            tS += s[i] + "\t";
                        }
                        heads.add(hS.trim());
                        fnames.add(s[s.length - 2]);
                        begins.add(b);
                        ends.add(e);
                        tails.add(tS.trim());
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

    public static void writeFile(String fname, ArrayList<String> hs, ArrayList<String> bs, 
            ArrayList<String> ts) {

        try {
            PrintWriter out = getPrintWriter(fname);
            for (int i = 0 ; i < hs.size(); i++) {
                String str = hs.get(i) + bs.get(i) + "\t" + ts.get(i);
                str = str.trim();
                if (i > 0 && hs.get(i - 1).trim().isEmpty() && str.isEmpty()) {
                    continue;
                }
                out.println(str);              
            }
            out.flush();
            out.close();
        } catch (IOException e) {
            e.printStackTrace ();
        }
    }
}
