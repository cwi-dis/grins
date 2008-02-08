import mailbox
import os

MAILDIR="/ufs/jack/Mail/inbox/httplogs"
LOGFOLDER="/ufs/jack/oratrix.com.logfiles"

class MyMHMailbox(mailbox.MHMailbox):
    def nextwithname(self):
        if not self.boxes:
            return None, None
        name = self.boxes[0]
        return name, mailbox.MHMailbox.next(self)

def savebodies(maildir, outfolder):
    existing = os.listdir(outfolder)
    mb = MyMHMailbox(maildir)
    name, msg = mb.nextwithname()
    while name:
        if not name in existing:
            outname = os.path.join(outfolder, name)
            ofp = open(outname, 'w')
            ofp.write(msg.fp.read())
        name, msg = mb.nextwithname()

if __name__ == '__main__':
    savebodies(MAILDIR, LOGFOLDER)
