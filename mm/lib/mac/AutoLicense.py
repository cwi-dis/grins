from licparser import *
import features

# This class has the same interface as licparser.License
# It represents an evaluation license that is automatically
# created when first running the program.
# This is a dummy implementation that always refuses to
# give a license (for platforms where we haven't implemented
# this yet).

class AutoEvaluateLicense:
    def __init__(self):
        raise Error, ""

    def have(self, *feat):
        return 1

    def need(self, *feat):
        return None

    def userinfo(self):
        return ''

    def is_evaluation_license(self):
        return 1
