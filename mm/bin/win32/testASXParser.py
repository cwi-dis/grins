# Test data for ASXParser
#

import sys
sys.path[0:0] = [r'd:\ufs\mm\cmif\pylib',r'd:\ufs\mm\cmif\lib',]

import ASXParser

data0="""<ASX version = "3.0">
    <Entry>
    <Abstract>Clip Description</Abstract>
    <Title>Clip Title</title>
    <Author>Author’s Name</Author>
<!-- This is a comment.
There are multiple Ref elements below. Only one piece of content will be connected to and played. If the URL in the first Ref element fails, the second Ref URL is tried. If it also fails, the third Ref URL is tried. If all three fail, the next Entry or EntryRef element in the ASX, if any, is processed. If there are no other Entry or EntryRef elements in the ASX the user receives an error message indicating that the content could not be found.
End comment. -->
        <Ref href = "mms://nsserver/pubpt/selection1.asf" />
        <Ref href = "mms://nsserver2/pubpt/selection1.asf" />
        <Ref href = "mms://nsbackup/pubpt/selection1.asf" />
    </Entry>
</ASX>
"""

data1="""<ASX Version = "3.0">
    <Title>The Something Catchy Station on Our Site</Title>
    <MoreInfo href = "http://www.server.com" />
<Entry>
    <Title>Catchy Tunes</title>
    <Abstract>Tunes you can’t get out of your head</abstract>
    <Copyright>Copyright© 1997 Company Name®</copyright>
    <Ref href = "http://server/catchy.asx" />
    <Ref href = "mms://backup/catchydown.asf" />

<!-- This is a comment. The first Ref element above points to an ASX file that contains information about a NetShow™ station. The second Ref element is only accessed if the first Ref fails. The second Ref element points to a stored ASF file that is a short message that the station is currently unavailable. End of comment -->

</Entry>
</ASX>
"""

data2="""<ASX version = "3.0" BannerBar = "FIXED">
        <Title>Show title</Title>
    <Logo href = "http://server/logos/mark1.jpg" style = "MARK" />
    <MoreInfo href = "http://server/main" />

<Entry ClientSkip = "no">
    <Ref href = "http://www.server/content.asf" />
    <Banner href = "http://server/logos/image2.gif">
    <MoreInfo href = "http://server/main" />
    <Abstract>Click here to find out about our company</Abstract>
    </Banner>
</Entry>
    <Event Name = "Adlink" WhenDone = "RESUME">
        <EntryRef
            href = "http://adserver/Adlink.htm"
            ClientSkip = "no" />
    </Event>
</ASX>
"""


data3="""<ASX version = "3.0">
    <Entry>
        <Ref href = "mms://nsserver/clips/clip1.asf" />
    </Entry>
<!-- This is a comment.
The Entry elements between the Repeat tags below each play the number of times defined by the Count attribute.
End comment. -->
    <Repeat Count = "2">
        <Entry><Ref href = "mms://nsserver/clips/clip2.asf" /></Entry>
        <Entry><Ref href = "mms://nsserver/clips/clip3.asf" /></Entry>
    </Repeat>
    <Entry>
        <Ref href = "mms://nsserver/clips/clip4.asf" />
    </Entry>
</ASX>
"""


# playlist
data4="""<ASX version = "3.0">
    <Title>Most requested titles of the day</Title>
    <Entry><Ref href = "mms://nsserver/content/title1.asf" /></Entry>
    <Entry><Ref href = "mms://nsserver/content/title2.asf" /></Entry>
    <Entry><Ref href = "mms://nsserver/content/title3.asf" /></Entry>
    <Entry><Ref href = "mms://nsserver/content/title4.asf" /></Entry>
</ASX>
"""

data5="""<asx><Entry>
    <PreviewDuration value = "0:30.0" />
    <Ref href = "mms://nsserver/content/selection.asf" />
</Entry></asx>
"""

data6="""<asx><Entry>
        <Duration value = "00:00:30" />
    <Ref href = "mms://nsserver/content/selection.asf" />
        </Entry>
</asx>
"""

data7="""<asx><Entry>
        <Duration value = "1:01.5" />    <!--This is also 61.5 seconds. -->
    <Ref href = "mms://nsserver/content/selection.asf" />
        </Entry>
</asx>
"""



if __name__ == '__main__':
    parser=ASXParser.ASXParser()
    parser.feed(data7)
    print 'Playlist:',parser._playlist
