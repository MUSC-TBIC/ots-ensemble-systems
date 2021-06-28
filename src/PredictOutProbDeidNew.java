
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.TreeMap;

/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

/**
 *
 * @author jun
 */
public class PredictOutProbDeidNew {

    /**
     * @param args the command line arguments
     */

    static HashMap<String, String> sm = new HashMap<String, String>();

    public static void main(String[] args) {

        // TODO code application logic here
        boolean test = false; // true: test, for the real, set false
        
        String del = "\t";
        String predictFile = "";
        String outDir = "";
        String ifReverse = "r";
        String thS = "0.6";
        String txtDir = "";
        String smFile = "";
        String year = "";

        if (test) {
            del = "1";
            predictFile = "data/sgd-2.0/crf/ts.pred";
            outDir = "data/i2b2_in/test/con2/";
            ifReverse = "r";
            thS = "0.6";
        } else {
            del = args[0];
            predictFile = args[1];
            outDir = args[2];
            ifReverse = args[3];
            thS = args[4];
            txtDir = args[5];
            smFile = args[6];
            year = args[7];
        }

        if (del.equals("1")) {
            del = " ";
        } else if (del.equals("2")) {
            del = "\t";
        } else {
            del = " ";
        }
        
        readMatchMap(sm, smFile);        
        
        ArrayList<String> inst = new ArrayList<String>();
        TreeMap<String, String> map = new TreeMap<String, String>();
        readData(predictFile, inst);
        
        double th = Double.parseDouble(thS);
        System.out.println(" " + th);
        readPredict(inst, map, del, ifReverse, th);

        writeListToFile(outDir, map, txtDir, year);
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
    
    public static void readPredict(ArrayList<String> inst, 
            TreeMap<String, String> map, String del, String ifReverse, double th) {
        
        int bCnt = 0;
        
        String cTag = "O";
        String nTag = "O";

        String begin = "";
        String end = "";
        String file = "";
        
        String sBegin = "0";
        //String sEnd = "0";

        boolean start = false;
							
        DecimalFormat df = new DecimalFormat("#.####");
        
        HashMap<String, Integer> ids = new HashMap<String, Integer>();
        
        for (int i = 0; i < inst.size(); i++) {

            String cStr = inst.get(i);
            String pStr = "";
            String nStr = "";
            String pTag = "O";
            
            if (i > 0) {
                pStr = inst.get(i - 1);
            } else {
                pTag = "O";
            }
            
            if (i < inst.size() - 1) {
                nStr = inst.get(i + 1);
            } else {
                nTag = "O";
            }
                    
            String cStrA[] = cStr.split(del);
            String pStrA[] = pStr.split(del);
            String nStrA[] = nStr.split(del);
            
            //<unk>	60	61	0	1	110-01.txt	O	O	0.9998
            //          -8      -7      -6      -5      -4              -3      -2      -1
            if (cStrA.length < 3) {
                cTag = "O";
            } else {
                begin = cStrA[cStrA.length - 8]; //5 -> 6
                end = cStrA[cStrA.length - 7]; //4 -> 5
                file = cStrA[cStrA.length - 4]; //3 -> 4
                cTag = cStrA[cStrA.length - 2];// gold -2 - > 3, ans -1 -> 2
            }

            if (pStrA.length < 3) {
                pTag = "O";
            } else {
                pTag = pStrA[pStrA.length - 2]; //ans -1 -> 2
            }
            
            if (nStrA.length < 3) {
                nTag = "O";
                //System.out.println("************");
            } else {
                nTag = nStrA[nStrA.length - 2];// ans -1 -> 2
            }

            if (cTag.startsWith("B-")) {
                
                bCnt++;
                
                if (nTag.startsWith("B-") || nTag.equals("O")) {

                    String cType = cTag.replace("B-","").toUpperCase();
                    String cType2 = sm.get(cType);
                    // check if cType2 is null ??
                    
                    double prob = Double.parseDouble(cStrA[cStrA.length - 1]);
                    if (prob > th) {
                    
                        if (ids.containsKey(file)) {
                            int idc = ids.get(file) + 1;
                            ids.put(file, idc);
                        } else {
                            ids.put(file, 0);
                        }

                        //"<DATE id=\"P0\" start=\"16\" end=\"26\" text=\"2106-02-12\" TYPE=\"DATE\" comment=\"\" />"
                        String aVal = "<" + cType2 + " id=\"P" + ids.get(file) + "\" start=\"" + begin + "\" end=\"" + end + "\" TYPE=\"" + cType + "\"";
                        String wTok = cStrA[0].replace("\"", "").replace("\\", "").replace("||", "");
                        aVal += " text=\"" + purgeString(wTok) + "\"";
                        //aVal += " prob=\"" + df.format(prob) + "\";"
                        aVal += "  />";

                        if (map.containsKey(file)) {
                            String val = map.get(file);
                            map.put(file, val + "\n" + aVal);
                        
                        } else {
                            map.put(file, aVal);
                        }                        
                    }
                    start = false;
                } else if (nTag.startsWith("I-")) {
                    start = true;
                    sBegin = begin;
                    //sEnd = end;
                } 
            } else if (cTag.startsWith("I-")) {
                if ((nTag.startsWith("B-") || nTag.equals("O"))) {
                    if (start) {
                        String wTok = ""; 
                        double prob = 0.0;
                        int len = 0;

                        int sSpan = Integer.parseInt(cStrA[cStrA.length - 8]);
                        int eSpan = Integer.parseInt(cStrA[cStrA.length - 7]);

                        for (int k = i; k >= 0 ; k--) {
                            if (inst.get(k).trim().isEmpty()) {
                                break;
                            }
                            String tmpA[] = inst.get(k).split(del);

                            int tmpB = Integer.parseInt(tmpA[tmpA.length - 8]);

                            if (tmpB < Integer.parseInt(sBegin)) {
                                break;
                            }

                            wTok = tmpA[0] + " " + wTok;
                            if (tmpB == Integer.parseInt(sBegin)) {
                                sSpan = tmpB;
                            }

                            prob += Double.parseDouble(tmpA[tmpA.length - 1]);
                            len++;
                        }
                        wTok = wTok.replace("\"", "").replace("\\", "").replace("||", "").trim();
                        prob /= (len + 1);

                        String cType = cTag.replace("I-","").toUpperCase();
                        String cType2 = sm.get(cType);

                        if (prob > th) {

                            if (ids.containsKey(file)) {
                                int idc = ids.get(file) + 1;
                                ids.put(file, idc);
                            } else {
                                ids.put(file, 0);
                            }

                            //"<DATE id=\"P0\" start=\"16\" end=\"26\" text=\"2106-02-12\" TYPE=\"DATE\" comment=\"\" />"
                            String aVal = "<" + cType2 + " id=\"P" + ids.get(file) + "\" start=\"" + sSpan + "\" end=\"" + eSpan + "\" TYPE=\"" + cType + "\"";
                            aVal += " text=\"" + purgeString(wTok) + "\"";
                            //aVal += " prob=\"" + df.format(prob) + "\";"
                            aVal += "  />";

                            if (map.containsKey(file)) {
                                String val = map.get(file);
                                map.put(file, val + "\n" + aVal);
                            } else {
                                map.put(file, aVal);
                            }
                            start = false;
                        }
                    }
                } else if (nTag.startsWith("I-")) {
                    start = true;
                }
            } else if (cTag.equals("O")) {
                start = false;
            }

        }
        
        System.out.println("concept out: " + bCnt);
    }

    public static void readData(String file, ArrayList<String> inst) {

        String str = "";
        {
            BufferedReader txtin = null;
            try {
                txtin = new BufferedReader(new FileReader(file));

                while ((str = txtin.readLine()) != null) {
                    inst.add(str.trim());
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
    
    public static PrintWriter getPrintWriter (String file)
    throws IOException {
        return new PrintWriter (new BufferedWriter
                (new FileWriter(file)));
    }

    public static void writeListToFile(String dir, TreeMap<String, String> map, String txtDir, String year) {

        Iterator<String> it = map.keySet().iterator();
        while (it.hasNext()) {
            String key = it.next();
            String val = map.get(key);

            String txtFile = txtDir + key.replace(".txt", ".xml");
            ArrayList<String> txts = new ArrayList<String>();
            readTxtFile(txtFile, txts);
            
            writeList(dir + key.replace(".txt", ".xml"), val, txts, year);
        }
    }

    public static void writeList(String file, String str, ArrayList<String> txts, String year) {

        try {
            PrintWriter out = getPrintWriter(file);
            
            for (String t : txts) {
                out.println(t);
            }
            out.println("<TAGS>");
            out.println(str);

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

    public static String purgeString(String in) {
        StringBuffer out = new StringBuffer(); // Used to hold the output.
        char c; // Used to reference the current character.

        if (in == null || ("".equals(in))) return ""; // vacancy test.
        for (int i = 0; i < in.length(); i++) {
            c = in.charAt(i); // NOTE: No IndexOutOfBoundsException caught here; it should not happen.
            if (Character.isAlphabetic(c) || Character.isDigit(c)) {
                out.append(c);
            }
        }
        return out.toString();
    }    
}
