import cmifex
import cmifex2

h0 = cmifex.CreateWindow("test",20,20,400,400,1)
#h2 = cmifex2.CreateDialogbox("Dialog",h0,20,20,400,400)
#h1 = cmifex2.CreateButton("button",h2,10,10,150,100)
#h3 = cmifex2.CreateButton("button",h1,10,10,60,80)
#h3 = cmifex2.CreateButton("button",h1,80,10,60,80)
l = 10
t = 10
w = 50
h = 20
r, b = l + w, t + h
l = l+1
t = t+1
r = r-1
b = b-1
l1 = l - 1
t1 = t - 1
r1 = r
b1 = b
ll = l + 2
tt = t + 2
rr = r - 2
bb = b - 3

cmifex2.DrawRect(h0, (l1, t1, ll, tt, ll, bb, l1, b1), 255, 0, 0)
for x in range(1,100000):
	pass
cmifex2.DrawRect(h0, (l1, t1, r1, t1, rr, tt, ll, tt), 0, 255, 0)
for x in range(1,100000):
	pass
cmifex2.DrawRect(h0, (r1, t1, r1, b1, rr, bb, rr, tt), 0, 0, 255)
for x in range(1,100000):
	pass
cmifex2.DrawRect(h0, (l1, b1, ll, bb, rr, bb, r1, b1), 0, 0, 0)
#gc.FillPolygon([(l1, t1), (ll, tt), (ll, bb), (l1, b1)],
#    X.Convex, X.CoordModeOrigin)

#gc.FillPolygon([(l1, t1), (r1, t1), (rr, tt), (ll, tt)],
#	       X.Convex, X.CoordModeOrigin)

#gc.FillPolygon([(r1, t1), (r1, b1), (rr, bb), (rr, tt)],
#		       X.Convex, X.CoordModeOrigin)

#gc.FillPolygon([(l1, b1), (ll, bb), (rr, bb), (r1, b1)],
#			       X.Convex, X.CoordModeOrigin)

l = 200
t = 40
w = 150
h = 100
r = l + w
b = t + h
x = l + w/2
y = t + h/2
n = int(3.0 * w / h + 0.5)
ll = l + n
tt = t + 3
rr = r - n
bb = b - 3

cmifex2.DrawRect(h0, (l, y, x, t, x, tt, ll, y), 255, 0, 0)
for s in range(1,100000):
	pass
cmifex2.DrawRect(h0, (x, t, r, y, rr, y, x, tt), 0, 255, 0)
for s in range(1,100000):
	pass
cmifex2.DrawRect(h0, (r, y, x, b, x, bb, rr, y), 0, 0, 255)
for s in range(1,100000):
	pass
cmifex2.DrawRect(h0, (l, y, ll, y, x, bb, x, b), 0, 0, 0)

#gc.FillPolygon([(l, y), (x, t), (x, tt), (ll, y)],
#				       X.Convex, X.CoordModeOrigin)

#gc.FillPolygon([(x, t), (r, y), (rr, y), (x, tt)],
#				       X.Convex, X.CoordModeOrigin)

#gc.FillPolygon([(r, y), (x, b), (x, bb), (rr, y)],
#			       X.Convex, X.CoordModeOrigin)

#gc.FillPolygon([(l, y), (ll, y), (x, bb), (x, b)],
#				       X.Convex, X.CoordModeOrigin)
