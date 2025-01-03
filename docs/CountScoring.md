<!-- module: mir.ir.impls.count_scoring_function -->

## Count Scoring


The CountScoringFunction class implements a simple scoring function that calculates the score of a document based on the ratio of the number of terms matching the query to the number of query terms.

It returns this ratio as the document's score. 

This scoring function is basic and doesn't take into account term frequency or document length.