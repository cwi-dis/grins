import cmifex
import cmifex2

#h1 = cmifex.CreateWindow("τέστ",20,20,400,400,1)
h = cmifex2.CreateDialogbox("Dialog",0,20,20,400,400,1)
c = cmifex2.CreateButton("Static",h,10,10,50,20,('p',''))
c2 = cmifex2.CreateEdit("",h,70,10,100,20,0)
c3 = cmifex2.CreateListbox("",h,180,10,50,100,1)
c4 = cmifex2.CreateMultiEdit("this is a test",h,70,40,100,55,1)
c5 = cmifex2.CreateCombobox("",h,10,100,100,100,(1,'dr',1))
c6 = cmifex2.CreateButton("radio right",h,240,10,110,20,('r',''))
c7 = cmifex2.CreateButton("radio left",h,240,40,110,20,('r','left'))
c8 = cmifex2.CreateButton("checkbox right",h,240,70,110,20,('t',''))
c9 = cmifex2.CreateButton("checkbox left",h,240,100,110,20,('t','left'))
g = cmifex2.CreateGroupBox("",h,120,140,200,150)
g1 = cmifex2.CreateButton("radio right",g,10,20,150,20,('r',''))
g2 = cmifex2.CreateButton("radio right",g,10,40,150,20,('r',''))
g3 = cmifex2.CreateButton("radio right",g,10,60,150,20,('r',''))
s1 = cmifex2.CreateContainerbox(h,10,300,150,40)
