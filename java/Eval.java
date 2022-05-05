/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */



import java.io.*;
import java.text.DecimalFormat;
import java.text.NumberFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedHashMap;
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
public class Eval {

    /**
     * @param args the command line arguments
     */

    static HashMap<String, String> sm = new HashMap<String, String>();
    static ArrayList<String> cat = new ArrayList<String>();
    static ArrayList<String> sub = new ArrayList<String>();
    
    static double f1d = 0.0;
    static double rd = 0.0;
    static double pd = 0.0;
    static double f2d = 0.0;
    static double f_2d = 0.0;
    
    public static double getF1() {
        return f1d;
    }
    
    public static void main(String[] args) {
    }
    
    public static void test(String refDir, String ansDir, String year) {
        sm.put("DOCTOR","NAME");
        sm.put("PATIENT","NAME");
        sm.put("USERNAME","NAME");
        sm.put("PROFESSION","PROFESSION");
        sm.put("CITY","LOCATION");
        sm.put("COUNTRY","LOCATION");
        sm.put("HOSPITAL","LOCATION");
        sm.put("LOCATION-OTHER","LOCATION");
        sm.put("ORGANIZATION","LOCATION");
        sm.put("STATE","LOCATION");
        sm.put("STREET","LOCATION");
        sm.put("ZIP","LOCATION");
        sm.put("AGE","AGE");
        sm.put("DATE","DATE");
        sm.put("EMAIL","CONTACT");
        sm.put("FAX","CONTACT");
        sm.put("PHONE","CONTACT");
        sm.put("URL","CONTACT");
        sm.put("BIOID","ID");
        sm.put("DEVICE","ID");
        sm.put("HEALTHPLAN","ID");
        sm.put("IDNUM","ID");
        sm.put("MEDICALRECORD","ID");
        sm.put("LICENSE","ID");
        
        cat.add("NAME");
        cat.add("PROFESSION");
        cat.add("LOCATION");
        cat.add("AGE");
        cat.add("DATE");
        cat.add("CONTACT");
        cat.add("ID");
        
        sub.add("DOCTOR");
        sub.add("PATIENT");
        sub.add("USERNAME");
        sub.add("PROFESSION");
        sub.add("CITY");
        sub.add("COUNTRY");
        sub.add("HOSPITAL");
        sub.add("LOCATION-OTHER");
        sub.add("ORGANIZATION");
        sub.add("STATE");
        sub.add("STREET");
        sub.add("ZIP");
        sub.add("AGE");
        sub.add("DATE");
        sub.add("EMAIL");
        sub.add("FAX");
        sub.add("PHONE");
        sub.add("URL");
        sub.add("BIOID");
        sub.add("DEVICE");
        sub.add("HEALTHPLAN");
        sub.add("IDNUM");
        sub.add("MEDICALRECORD");
        sub.add("LICENSE");

        doEval(refDir, ansDir, year);        
    }
    
    public static void test() {

        sm.put("DOCTOR","NAME");
        sm.put("PATIENT","NAME");
        sm.put("USERNAME","NAME");
        sm.put("PROFESSION","PROFESSION");
        sm.put("CITY","LOCATION");
        sm.put("COUNTRY","LOCATION");
        sm.put("HOSPITAL","LOCATION");
        sm.put("LOCATION-OTHER","LOCATION");
        sm.put("ORGANIZATION","LOCATION");
        sm.put("STATE","LOCATION");
        sm.put("STREET","LOCATION");
        sm.put("ZIP","LOCATION");
        sm.put("AGE","AGE");
        sm.put("DATE","DATE");
        sm.put("EMAIL","CONTACT");
        sm.put("FAX","CONTACT");
        sm.put("PHONE","CONTACT");
        sm.put("URL","CONTACT");
        sm.put("BIOID","ID");
        sm.put("DEVICE","ID");
        sm.put("HEALTHPLAN","ID");
        sm.put("IDNUM","ID");
        sm.put("MEDICALRECORD","ID");
        sm.put("LICENSE","ID");
                
        cat.add("NAME");
        cat.add("PROFESSION");
        cat.add("LOCATION");
        cat.add("AGE");
        cat.add("DATE");
        cat.add("CONTACT");
        cat.add("ID");
        
        sub.add("DOCTOR");
        sub.add("PATIENT");
        sub.add("USERNAME");
        sub.add("PROFESSION");
        sub.add("CITY");
        sub.add("COUNTRY");
        sub.add("HOSPITAL");
        sub.add("LOCATION-OTHER");
        sub.add("ORGANIZATION");
        sub.add("STATE");
        sub.add("STREET");
        sub.add("ZIP");
        sub.add("AGE");
        sub.add("DATE");
        sub.add("EMAIL");
        sub.add("FAX");
        sub.add("PHONE");
        sub.add("URL");
        sub.add("BIOID");
        sub.add("DEVICE");
        sub.add("HEALTHPLAN");
        sub.add("IDNUM");
        sub.add("MEDICALRECORD");
        sub.add("LICENSE");
        
        String subDir = "con_rnn2";
        //subDir = "con_neuXml";
        //subDir = "con_vote";
        //subDir = "con_bks";
        //subDir = "con_dtm";
        //subDir = "con_mitie";
        //subDir = "con_soft";
        //subDir = "con_crf";
        //subDir = "con_vw";
        
        String refDir = "data/i2b2/2014deid/test/xml/";
        String ansDir = "data/i2b2/2014deid/test/" + subDir + "/";
        String year = "2014";
        doEval(refDir, ansDir, year);
    }
    
    public static void doEval(String refDir, String ansDir, String year) {

        ArrayList<String> refFileList = new ArrayList<String>();
        listFile(refDir, refFileList);
        
        ArrayList<String> refs = new ArrayList<String>();
        for (String fileName : refFileList) {
            parse(refDir, fileName, refs, year);
        }

        ArrayList<String> ansFileList = new ArrayList<String>();
        listFile(ansDir, ansFileList);
        // parse each file
        ArrayList<String> anss = new ArrayList<String>();
        for (String fileName : ansFileList) {
            parse(ansDir, fileName, anss, year);
        }
        
        doAnalExact(refs, anss);
    }

    public static void doAnalExact(ArrayList<String> refs, ArrayList<String> anss) {
        
        LinkedHashMap<String, ArrayList<String>> rMap = new LinkedHashMap<String, ArrayList<String>>();
        LinkedHashMap<String, ArrayList<String>> aMap = new LinkedHashMap<String, ArrayList<String>>();
                
        for (String key: refs) {
            addKeys(rMap, key);
        }
        
        for (String key: anss) {
            addKeys(aMap, key);
        }
        
        /*
        for (String key: cat) {
            String nK = "c " + key;
            if (rMap.containsKey(nK) && aMap.containsKey(nK)) {
                calcExact(key, rMap.get(nK), aMap.get(nK));
            }
        }
        for (String key: sub) {
            String nK = "s " + key;
            if (rMap.containsKey(nK) && aMap.containsKey(nK)) {
                calcExact(key, rMap.get(nK), aMap.get(nK));
            }
        }
        */        
        calcExact("All", rMap.get("All"), aMap.get("All"));
    }
    
    public static void addKeys(LinkedHashMap<String, ArrayList<String>> map, String key) {
            
        String s[] = key.split("\\|");
        String ca = "c " + s[4];
        String su = "s " + s[3];

        if (!map.containsKey(ca)) {
            ArrayList<String> tmp = new ArrayList<String>();
            tmp.add(key);
            map.put(ca, tmp);
        } else {
            map.get(ca).add(key);
        }
        if (!map.containsKey(su)) {
            ArrayList<String> tmp = new ArrayList<String>();
            tmp.add(key);
            map.put(su, tmp);
        } else {
            map.get(su).add(key);
        }                               
        if (!map.containsKey("All")) {
            ArrayList<String> tmp = new ArrayList<String>();
            tmp.add(key);
            map.put("All", tmp);
        } else {
            map.get("All").add(key);
        }                               
    }
    
    public static void calcExact(String categ, ArrayList<String> refs, ArrayList<String> anss) {
    
        double refSize = refs.size();
        double ansSize = 0;
        
        if (anss != null) {
            ansSize = anss.size();
        }

        int cor = 0;
        for (String key: refs) {
            if (anss != null && anss.contains(key)) {
                cor++;
            } 
        }
        
        double r = (cor * 100)/ refSize;
        double p = 0;
        if (ansSize != 0) {
            p = (cor * 100)/ ansSize;
        }
        double f1 = 0;
        if (p + r != 0) {
            f1 = (2*p*r) / (p + r);
        }
        
        NumberFormat nf = new DecimalFormat("###.00");        
        System.out.println(categ + "\t" + nf.format(p) + "\t" + nf.format(r) + "\t" + nf.format(f1)); // recall
        
        if (categ.equals("All")) {
            f1d = f1;
            rd = r;
            pd = p;
            f2d = 0;
            f_2d = 0;
            if (p + r != 0) {
                f2d = (double) (5*p*r) / (double) (4*p + r);
            }
            if (p + r != 0) {
                //f_2d = (double) (1.25*p*r) / (double) (0.25*p + r);
                f_2d = (double) (1.5625*p*r) / (double) (0.5625*p + r); // 0.75
            }
            
            //System.out.println(refSize + "\t" + ansSize + "\t" + cor); // recall
        }
        
    }
    
    public static void updateMap(TreeMap<String, Integer> map, String key) {
        if (map.containsKey(key)) {
            int val = map.get(key) + 1;
            map.put(key, val);
        } else {
            map.put(key, 1);
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

    public static void parse(String inDir, String fileName, ArrayList<String> outs, String year) {

        String str = "";
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
                String type1 = t.attr("type");
                String cType = t.tagName();               
                outs.add(fileName + "|" + start + "|" + end + "|" + type1.toUpperCase() + "|" + cType.toUpperCase());                
            }
        }
    }

}
