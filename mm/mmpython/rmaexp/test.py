
import rma

engine = rma.CreateEngine()

player =  engine.CreatePlayer()

context = rma.CreateClientContext()

player.SetClientContext(context)


# real audio
url1="file://D|/ufs/mm/cmif/mmpython/rmasdk/testdata/thanks3.ra"

# real video
url2="file://D|/ufs/mm/cmif/mmpython/rmasdk/testdata/test.rv"

# real text
url3="file://D|/ufs/mm/cmif/mmpython/rmasdk/testdata/news.rt"

# real pixel
url4="file:///D|/ufs/mm/cmif/mmpython/rmasdk/testdata/fadein.rp"


player.OpenURL(url1)

player.Begin()

