from knackpy.exceptions.exceptions import ValidationError

import pdb

class Record:
    """ Knack field wrapper """
    def __repr__(self):
        length = len(self.__dict__.keys())
        return f"<Record [{length} fields]>"

    def __init__(self, **kwargs):
        pass
