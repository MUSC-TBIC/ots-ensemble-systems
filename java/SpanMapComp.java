
import java.util.Comparator;

public class SpanMapComp implements Comparator<String> {
 
    @Override
    public int compare(String o1, String o2) {
        //start + " " + end + " " + type1
        String oA1[] = o1.split(" ", 3);
        String oA2[] = o2.split(" ", 3);

        int s1 = Integer.parseInt(oA1[0]);
        int s2 = Integer.parseInt(oA2[0]);

        if (s1 != s2) {
            return new Integer(s1).compareTo(s2);
        } else {
            int e1 = Integer.parseInt(oA1[1]);
            int e2 = Integer.parseInt(oA2[1]);
            if (e1 != e2) {
                return new Integer(e1).compareTo(e2);
            } else {
                return oA1[2].compareTo(oA2[2]);
            }
        }
    }
}    

