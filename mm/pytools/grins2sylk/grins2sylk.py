import sys
import string
import time
import mailbox
import rfc822
import sylk


# Extracting and formatting helpers

def my_date(msg, field):
    date = msg.getdate(field)
    if not date:
        return ""
    return time.strftime("%d-%m-%Y", date)

def my_email(msg, field):
    fullname, email = msg.getaddr(field)
    if not email:
        return ""
    return email

def my_toplevel(msg, field):
    email = my_email(msg, field)
    if not email:
        return email
    temp = string.split(email, "@")
    if len(temp) != 2:
        return ""
    temp = string.split(temp[1], ".")
    return temp[-1]

def my_yesno(msg, field):
    yesno = msg.getheader(field)
    if not yesno:
        return 0
    yesno = string.lower(yesno)
    if yesno == "yes":
        return 1
    if yesno == "no" or yesno == "":
        return 0
    return 0

#
# Here are the mail driving table and formatting routine.

FIELDS=["date", "email", "toplevel", "country", "windows", "mac",
        "sgi", "sun", "editor", "maillist", "smil", "g2", "netshow",
        "quicktime", "dhtml", "htmltime", "multilang", "adaptive",
        "accessability"]

def getdata(header, body):
    data = {}
    data["date"] = my_date(header, "date")
    data["email"] = my_email(body, "email")
    data["toplevel"] = my_toplevel(body, "email")
    data["country"] = body.getheader("country")
    data["windows"] = my_yesno(body, "want-windows")
    data["mac"] = my_yesno(body, "want-mac")
    data["sgi"] = my_yesno(body, "want-sgi")
    data["sun"] = my_yesno(body, "want-sun")
    data["editor"] = my_yesno(body, "want-editor")
    data["maillist"] = my_yesno(body, "want-maillist")
    data["smil"] = my_yesno(body, "need-smil")
    data["g2"] = my_yesno(body, "need-g2")
    data["netshow"] = my_yesno(body, "need-netshow")
    data["quicktime"] = my_yesno(body, "need-quicktime")
    data["dhtml"] = my_yesno(body, "need-dhtml")
    data["htmltime"] = my_yesno(body, "need-htmltime")
    data["multilang"] = my_yesno(body, "need-multilang")
    data["adaptive"] = my_yesno(body, "need-adaptive")
    data["accessability"] = my_yesno(body, "need-accessability")

    return data

def testdata(header):
    subject =  header.getheader("subject")
    if not subject: return 0
    if subject != "GRiNS Request":
        return 0
    return 1

class Converter:

    def __init__(self, fields, getdata, testdata):
        self.mailbox = mailbox
        self.fields = fields
        self.getdata = getdata
        self.testdata = testdata

    def run(self, mailbox):
        self.output = [self.fields]
        while 1:
            msg = mailbox.next()
            if not msg: break
            self.runone(msg)
        return self.output

    def runone(self, msg):
        header = msg
        if not self.testdata(header):
            return
        msg.rewindbody()
        dummy = msg.fp.readline()
        body = rfc822.Message(msg.fp)
        data = self.getdata(header, body)
        list = []
        for field in self.fields:
            list.append(data[field])
        self.output.append(list)

def main():
    if len(sys.argv) != 3:
        print "Usage: %s mh-directory outputfile"%sys.argv[0]
        sys.exit(1)
    conv = Converter(FIELDS, getdata, testdata)
    mbox = mailbox.MHMailbox(sys.argv[1])
    data = conv.run(mbox)
    fp = open(sys.argv[2], "w")
    sylk.write_sylk(fp, data, id="GRiNSrequests")
    fp.close()

if __name__ == "__main__":
    main()
