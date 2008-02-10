__version__ = "$Id$"

class StringTokenizer:
    def __init__(self, str, delim=' \t\n\r\f'):
        self.__str = str
        self.__delim = delim
        self.__pos = 0
        self.__maxpos = len(str)
    def hasMoreTokens(self):
        return (self.__pos < self.__maxpos)
    def nextToken(self):
        if self.__pos >= self.__maxpos:
            raise None
        start = self.__pos
        while self.__pos < self.__maxpos and self.__delim.find(self.__str[self.__pos])<0:
            self.__pos = self.__pos + 1
        if start == self.__pos and self.__delim.find(self.__str[self.__pos])>=0:
            self.__pos = self.__pos + 1
        return self.__str[start:self.__pos]

class StringSplitter:
    def __init__(self, str, delim=' ,'):
        self.__str = str
        self.__delim = delim
        self.__pos = 0
        self.__maxpos = len(str)
    def hasMoreTokens(self):
        while self.__pos < self.__maxpos and self.__delim.find(self.__str[self.__pos])>=0:
            self.__pos = self.__pos + 1
        return (self.__pos < self.__maxpos)
    def nextToken(self):
        while self.__pos < self.__maxpos and self.__delim.find(self.__str[self.__pos])>=0:
            self.__pos = self.__pos + 1
        if self.__pos == self.__maxpos:
            return None
        start = self.__pos
        while self.__pos < self.__maxpos and self.__delim.find(self.__str[self.__pos])<0:
            self.__pos = self.__pos + 1
        return self.__str[start:self.__pos]

def splitlist(str, delims=' ,'):
    st = StringSplitter(str, delims)
    L = []
    token = st.nextToken()
    while token:
        L.append(token)
        token = st.nextToken()
    return L
