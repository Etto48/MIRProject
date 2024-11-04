from mir.ir.scoring_function import ScoringFunction


class CountScoringFunction(ScoringFunction):
    def __call__(self, document, postings, query):
        return len(postings) / len(query)