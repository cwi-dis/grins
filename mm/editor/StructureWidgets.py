# These are the standard views for a structure.

# TODO: rename everything to "widgets"

import Widgets
import Bandwidth
import MMurl, MMAttrdefs, MMmimetypes, MMNode
import features
import os
import settings
from AppDefaults import *

# remove this. TODO
import whrandom


def create_MMNode_widget(node, root):
    #assert root != None
    ntype = node.GetType()
    if ntype == 'seq':
        return SeqWidget(node, root)
    elif ntype == 'par':
        return ParWidget(node, root)
    elif ntype == 'alt':                # The switch
        return SwitchWidget(node, root)
    elif ntype == 'ext':
        return MediaWidget(node, root)
    # TODO: test for a realmedia MMslide node.
    elif ntype == 'imm':
#        print "TODO: Got an imm node."
        return MediaWidget(node, root)
    elif ntype == 'excl':
        return ExclWidget(node, root)
    elif ntype == 'prio':
        return PrioWidget(node, root)
    else:
        print "DEBUG: Error! I am not sure what sort of node this is!! StructureViews.py:12"
        print "Node appears to be a ", ntype
        return None

class MMNodeWidget(Widgets.Widget):
    # View of a Node within the Hierarchy view
    def __init__(self, node, root):
        Widgets.Widget.__init__(self, root)
        self.node = node               # : MMNode
        assert isinstance(node, MMNode.MMNode)
        self.node.views['struct_view'] = self
        self.name = MMAttrdefs.getattr(self.node, 'name')
        
    def destroy(self):
        # Prevent cyclic dependancies.
        Widgets.Widget.destroy(self)
        del self.node.views['struct_view']
        self.node = None
        
    #
    # Menu handling functions, aka callbacks.
    #

##  def helpcall(self):
##      import Help
##      Help.givehelp('Hierarchy_view')

    def select(self):
        Widgets.Widget.select(self)

    def expandcall(self):
        # 'Expand' the view of this node.
        #assert 0
        self.root.toplevel.setwaiting()
        if hasattr(self.node, 'expanded'):
            collapsenode(self.node)
        else:
            expandnode(self.node)
        self.root.recalc()

    def expandallcall(self, expand):
        # Expand the view of this node and all kids.
        #assert 0
        self.root.toplevel.setwaiting()
        if do_expand(self.node, expand, None, 1):
            # there were changes
            # make sure root isn't collapsed
            self.root.recalc()

    def playcall(self):
        top = self.root.toplevel
        top.setwaiting()
        top.player.playsubtree(self.node)

    def playfromcall(self):
        top = self.root.toplevel
        top.setwaiting()
        top.player.playfrom(self.node)

    def attrcall(self):
        self.root.toplevel.setwaiting()
        import AttrEdit
        AttrEdit.showattreditor(self.root.toplevel, self.node)

    def infocall(self):
        self.root.toplevel.setwaiting()
        import NodeInfo
        NodeInfo.shownodeinfo(self.root.toplevel, self.node)

    def editcall(self):
        self.root.toplevel.setwaiting()
        import NodeEdit
        NodeEdit.showeditor(self.node)
    def _editcall(self):
        self.root.toplevel.setwaiting()
        import NodeEdit
        NodeEdit._showeditor(self.node)
    def _opencall(self):
        self.root.toplevel.setwaiting()
        import NodeEdit
        NodeEdit._showviewer(self.node)

    def anchorcall(self):
        self.root.toplevel.setwaiting()
        import AnchorEdit
        AnchorEdit.showanchoreditor(self.root.toplevel, self.node)

    def createanchorcall(self):
        self.root.toplevel.links.wholenodeanchor(self.node)

    def hyperlinkcall(self):
        self.root.toplevel.links.finish_link(self.node)

    def focuscall(self):
        top = self.root.toplevel
        top.setwaiting()
        if top.channelview is not None:
            top.channelview.globalsetfocus(self.node)

    def deletecall(self):
        self.root.deletefocus(0)

    def cutcall(self):
        self.root.deletefocus(1)

    def copycall(self):
        root = self.root
        root.toplevel.setwaiting()
        root.copyfocus()

    def createbeforecall(self, chtype=None):
        self.root.create(-1, chtype=chtype)

    def createbeforeintcall(self, ntype):
        self.root.create(-1, ntype=ntype)

    def createaftercall(self, chtype=None):
        self.root.create(1, chtype=chtype)

    def createafterintcall(self, ntype):
        self.root.create(1, ntype=ntype)

    def createundercall(self, chtype=None):
        self.root.create(0, chtype=chtype)

    def createunderintcall(self, ntype):
        self.root.create(0, ntype=ntype)

    def createseqcall(self):
        self.root.insertparent('seq')

    def createparcall(self):
        self.root.insertparent('par')

    def createbagcall(self):
        self.root.insertparent('bag')

    def createaltcall(self):
        self.root.insertparent('alt')

    def pastebeforecall(self):
        self.root.paste(-1)

    def pasteaftercall(self):
        self.root.paste(1)

    def pasteundercall(self):
        self.root.paste(0)
        
class StructureObjWidget(MMNodeWidget):
    # TODO: make this inherit only from Widgets.Widget and aggregate a list.
    # A view of a seq, par, excl or something else that might exist.
    def __init__(self, node, root):
        MMNodeWidget.__init__(self, node, root)
        assert self is not None
        # Create more nodes under me if there are any.
        self.children = []
        self.collapsed = 0;             # Whether this node is collapsed or not.
        self.collapsebutton = CollapseButtonWidget(self, root);
        for i in self.node.children:
            bob = create_MMNode_widget(i, root)
            if bob == None:
                print "TODO: you haven't written all the code yet, have you Mike?"
            else:
                self.children.append(bob)

    def destroy(self):
        MMNodeWidget.destroy(self)
        self.children = None

    def collapse(self):
        self.collapsed = 1;
    def uncollapse(self):
        self.collapsed = 0;

    def get_obj_at(self, pos):
        # Return the MMNode widget at position x,y
        # Oh, how I love recursive methods :-). Nice. -mjvdg.
        if self.is_hit(pos):
            for i in self.children:
                ob = i.get_obj_at(pos)
                if ob != None:
                    return ob
            return self
        else:
            return None

    def recalc(self):
        self.collapsebutton.recalc();

    def draw(self, displist):
        # This is a base class for other classes.. this code only gets
        # called once the aggregating node has been called.
        # Draw only the children.
        if not self.collapsed:
            for i in self.children:
                i.draw(displist)

        # Draw the title.
        displist.fgcolor(CTEXTCOLOR);
        displist.usefont(f_title)
        l,t,r,b = self.pos_rel;
        b = t + self.get_rely(sizes_notime.TITLESIZE) + self.get_rely(sizes_notime.VEDGSIZE);
        l = l + self.get_relx(16);      # move it past the icon.
        displist.centerstring(l,t,r,b, self.name)
        self.collapsebutton.draw(displist);

class SeqWidget(StructureObjWidget):
    def __init__(self, node, root):
        self.dropbox = DropBoxWidget(root);
        StructureObjWidget.__init__(self, node, root);
    
    def draw(self, display_list):
        if self.selected: 
            display_list.drawfbox(self.highlight(SEQCOLOR), self.get_box())
            display_list.draw3dbox(FOCUSRIGHT, FOCUSBOTTOM, FOCUSLEFT, FOCUSTOP, self.get_box());
        else:
            display_list.drawfbox(SEQCOLOR, self.get_box())
            display_list.draw3dbox(FOCUSLEFT, FOCUSTOP, FOCUSRIGHT, FOCUSBOTTOM, self.get_box());

        if self.root.pushbackbars:
            for i in self.children:
                if isinstance(i, MediaWidget):
                    i.pushbackbar.draw(display_list)

        StructureObjWidget.draw(self, display_list)
        if self.root.dropbox:
            self.dropbox.draw(display_list);

        assert self.node is not None

    def get_nearest_node_index(self, pos):
        # Return the index of the node at the specific drop position.
        assert self.is_hit(pos);
        x,y = pos;
        # Working from left to right:
        for i in range(len(self.children)):
            l,t,w,h = self.children[i].get_box();
            if x <= l+(w/2.0):
                return i;
        return -1;

    def get_minsize(self):
        # Return the minimum size that I can be.

        if len(self.children) == 0:
            boxsize = sizes_notime.MINSIZE + 2*sizes_notime.HEDGSIZE;
            return self.get_relx(boxsize), self.get_rely(boxsize);

        min_width = 0.0; min_height = 0.0
        
        for i in self.children:
            w, h = i.get_minsize()
            if self.root.pushbackbars and isinstance(i, MediaWidget):
                pushover = self.get_relx(i.downloadtime_lag);
                min_width = min_width + pushover;
            else:
                pushover = 0.0;
            #assert w < 1.0 and w > 0.0
            #assert h < 1.0 and h > 0.0
            min_width = min_width + w;
            if h > min_height:
                min_height = h
        xgap = self.get_relx(sizes_notime.GAPSIZE)
#        handle = self.get_relx(sizes_notime.HANDLESIZE);
#        droparea = self.get_relx(sizes_notime.DROPAREASIZE);
        #assert min_width < 1.0
        #assert min_height < 1.0

        #             current +   gaps between nodes  +  gaps at either end      
        min_width = min_width + xgap*( len(self.children)-1) + 2*self.get_relx(sizes_notime.HEDGSIZE)

        if self.root.dropbox:
            min_width = min_width + self.dropbox.get_minsize()[0] + xgap;

        min_height = min_height + 2*self.get_rely(sizes_notime.VEDGSIZE)
        # Add the title
        min_height = min_height + self.get_rely(sizes_notime.TITLESIZE);
        return min_width, min_height

    def get_minsize_abs(self):
        # Everything here calculated in pixels.

        if len(self.children) == 0:
            boxsize = sizes_notime.MINSIZE + 2*sizes_notime.HEDGSIZE;
            return boxsize, boxsize

        mw=0; mh=0
        for i in self.children:
            if self.root.pushbackbars and isinstance(i, MediaWidget):
                pushover = i.downloadtime_lag
            else:
                pushover = 0;
            w,h = i.get_minsize_abs()
            if h > mh: mh=h
            mw = mw + w + pushover;

        mw = mw + sizes_notime.GAPSIZE*(len(self.children)-1) + 2*sizes_notime.HEDGSIZE

        if self.root.dropbox:
            mw = mw + self.dropbox.get_minsize_abs()[0] + sizes_notime.GAPSIZE;

        mh = mh + 2*sizes_notime.VEDGSIZE
        # Add the title box.
        mh = mh + sizes_notime.TITLESIZE
        return mw, mh
        
    def recalc(self):
        # Untested.
        # Recalculate the position of all the contained boxes.
        # Algorithm: Iterate through each of the MMNodes children's views and find their minsizes.
        # Apportion free space equally, based on the size of self.
        # TODO: This does not test for maxheight()
        
        l, t, r, b = self.pos_rel
        min_width, min_height = self.get_minsize()

        free_width = ((r-l) - min_width)

        # Add the title        free

        t = t + self.get_rely(sizes_notime.TITLESIZE)
        min_height = min_height - self.get_rely(sizes_notime.TITLESIZE)
        
        if len(self.children) > 0:
            overhead_width = 2.0*self.get_relx(sizes_notime.HEDGSIZE) + float(len(self.children)-1)*self.get_relx(sizes_notime.GAPSIZE);
        else:
            overhead_width = 0;

        if self.root.dropbox:
            free_width = free_width-self.dropbox.get_minsize()[0];

        if free_width < 0.0:
#            print "Warning! free_width is less than 0.0!:", free_width
            free_width = 0.0

        l = float(l) + self.get_relx(sizes_notime.HEDGSIZE) #+ self.get_relx(sizes_notime.HANDLESIZE);
        t = float(t) + self.get_rely(sizes_notime.VEDGSIZE)

        b = float(b) - self.get_rely(sizes_notime.VEDGSIZE)

        for medianode in self.children:    # for each MMNode:
            if self.root.pushbackbars and isinstance(medianode, MediaWidget):
#                print "TODO: test downloadtime pushover and sequence lags."
                l = l +  self.get_relx(medianode.downloadtime_lag);
            w,h = medianode.get_minsize()
            if h > (b-t)+0.000001:               # If the node needs to be bigger than the available space...
                pass;
#                print "Error: Node is too tall! h=",h,"(b-t)=",b-t;
#                #assert 0               # This shouldn't happen because the minimum size of this node
                                        # has already been determined to be bigger than this in minsize()
            # Take a portion of the free available width, fairly.
            if free_width < 0.001:
                thisnode_free_width = 0.0
            else:
                thisnode_free_width = (float(w) / (min_width-overhead_width)) * free_width


##            print "       Seq thisnode free width = ", thisnode_free_width;
##            print "       w = ", w, " min_width=", min_width, "free_width=", free_width;
##            print "       node:", medianode, medianode.node;

            # Give the node the free width.
            r = l + w + thisnode_free_width
            
#            print "DEBUG: Repositioning node to ", l, t, r, b
            if r > 1.0:
#                print "ERROR!!! Node extends too far right.. clipping.."
                r = 1.0
            if b > 1.0:
#                print "ERROR!! Node extends too far down.. clipping.."
                b = 1.0
            if l > 1.0:
#                print "ERROR!! Node starts too far across.. clipping.."
                l = 1.0
                r = 1.0

            medianode.moveto((l,t,r,b))
            medianode.recalc()
            l = r + self.get_relx(sizes_notime.GAPSIZE)

        # Position the stupid drop-box at the end.
        w,h = self.dropbox.get_minsize();
#        print "DEBUG: dropbox coords are ", w, h
#        print "Moving dropbox to", l,t,(float(w)/min_width)*free_width,b

        # The dropbox takes up the rest of the free width.
        r = self.pos_rel[2]-self.get_relx(sizes_notime.HEDGSIZE);
        
        self.dropbox.moveto((l,t,r,b));

        StructureObjWidget.recalc(self);


class DropBoxWidget(Widgets.Widget):
    # This is the stupid drop-box at the end of a sequence. Looks like a
    # MediaWidget, acts like a MediaWidget, but isn't a MediaWidget.
    def draw(self, displist):
        displist.drawfbox(LEAFCOLOR, self.get_box());
        displist.draw3dbox(FOCUSLEFT, FOCUSTOP, FOCUSRIGHT, FOCUSBOTTOM, self.get_box());
    def get_minsize(self):
        return self.get_relx(sizes_notime.MINSIZE), self.get_rely(sizes_notime.MINSIZE);
    def get_minsize_abs(self):
        return sizes_notime.MINSIZE, sizes_notime.MINSIZE;
    # Hmm.. as I said. Easy.
        

class VerticalWidget(StructureObjWidget):
    def get_minsize(self):
        # Return the minimum size that I can be.
        min_width = 0; min_height = 0

        if len(self.children) == 0:
            boxsize = sizes_notime.MINSIZE + 2*sizes_notime.HEDGSIZE;
            return self.get_relx(boxsize), self.get_rely(boxsize);

        for i in self.children:
            w, h = i.get_minsize()
#            print "VerticalWidget: w and h are: ", w, h
#            #assert w < 1.0 and w > 0.0
            #assert h < 1.0 and h > 0.0
            if w > min_width:           # The width is the greatest of the width of all children.
                min_width = w
            min_height = min_height + h

        # Add the text label to the top.
        titleheight = self.get_rely(sizes_notime.TITLESIZE)
        min_height = min_height + titleheight;

        ygap = self.get_rely(sizes_notime.GAPSIZE)

        #assert min_width < 1.0
        #assert min_height < 1.0

        min_width = min_width + 2*self.get_relx(sizes_notime.HEDGSIZE)
        min_height = min_height + ygap*(len(self.children)-1) + 2.0*self.get_rely(sizes_notime.VEDGSIZE)

#        print "VerticalWidget: min_width is: ", min_width
#        #assert min_width < 1.0 and min_width > 0.0
        #assert min_height < 1.0 and min_height > 0.0

        return min_width, min_height

    def get_nearest_node_index(self, pos):
        # Return the index of the node at the specific drop position.
        assert self.is_hit(pos);
        x,y = pos;
        # Working from left to right:
        for i in range(len(self.children)):
            l,t,w,h = self.children[i].get_box();
            if y <= t+(h/2.0):
                return i;
        return -1;

    def get_minsize_abs(self):
        mw=0; mh=0

        if len(self.children) == 0:
            boxsize = sizes_notime.MINSIZE + 2*sizes_notime.HEDGSIZE;
            return boxsize, boxsize

        for i in self.children:
            w,h = i.get_minsize_abs()
            if w > mw: mw=w
            mh=mh+h
        mh = mh + sizes_notime.GAPSIZE*(len(self.children)-1) + 2*sizes_notime.VEDGSIZE
        # Add the titleheight
        mh = mh + sizes_notime.TITLESIZE
        mw = mw + 2*sizes_notime.HEDGSIZE
        return mw, mh

    def recalc(self):
        # Untested.
        # Recalculate the position of all the contained boxes.
        # Algorithm: Iterate through each of the MMNodes children's views and find their minsizes.
        # Apportion free space equally, based on the size of self.
        # TODO: This does not test for maxheight()

        l, t, r, b = self.pos_rel
        # Add the titlesize;
        t = t + self.get_rely(sizes_notime.TITLESIZE)
        min_width, min_height = self.get_minsize()
        min_height = min_height - self.get_rely(sizes_notime.TITLESIZE);

        overhead_height = 2.0*self.get_rely(sizes_notime.VEDGSIZE) + float(len(self.children)-1)*self.get_rely(sizes_notime.GAPSIZE)
        free_height = (b-t) - min_height
##        print "***"
##        print "DEBUG: Vertical: calculating free height";
##        print "min_width: ", min_width, "min_height: ", min_height
##        print "actual height: ", (b-t);
##        print "---";
        if free_height < 0.001 or free_height > 1.0:
#            print "Warning! free_height is wrong: ", free_height, self;
            free_height = 0.0

        l = float(l) + self.get_relx(sizes_notime.HEDGSIZE)
        r = float(r) - self.get_relx(sizes_notime.HEDGSIZE)
        t = float(t) + self.get_rely(sizes_notime.VEDGSIZE)
        

        for medianode in self.children:    # for each MMNode:
            w,h = medianode.get_minsize()
            if h > (b-t):               # If the node needs to be bigger than the available space...
                pass                   # TODO!!!!!
#                print "Error: Node is too big!"
#                #assert 0               # This shouldn't happen because the minimum size of this node
                                        # has already been determined to be bigger than this in minsize()
            # Take a portion of the free available width, fairly.
            if free_height == 0.0:
                thisnode_free_height = 0.0
            else:
                thisnode_free_height = (float(h)/(min_height-overhead_height)) * free_height
            # Give the node the free width.
            b = t + h + thisnode_free_height 
            # r = l + w # Wrap the node to it's minimum size.

            if r > 1.0:
#                print "ERROR!!! Node extends too far right.. clipping.."
                r = 1.0
            if b > 1.0:
#                print "ERROR!! Node extends too far down.. clipping.."
                b = 1.0
            if l > 1.0:
#                print "ERROR!! Node starts too far across.. clipping.."
                l = 1.0
                r = 1.0
                
            medianode.moveto((l,t,r,b))
            medianode.recalc()
            t = b + self.get_rely(sizes_notime.GAPSIZE)
        StructureObjWidget.recalc(self);

    def draw(self, display_list):
        if self.root.pushbackbars:
            for i in self.children:
                if isinstance(i, MediaWidget):
#                    print "Par: drawing bar";
                    i.pushbackbar.draw(display_list);
        StructureObjWidget.draw(self, display_list);


class ParWidget(VerticalWidget):
    def draw(self, display_list):
        if self.selected:
            display_list.drawfbox(self.highlight(PARCOLOR), self.get_box())
            display_list.draw3dbox(FOCUSRIGHT, FOCUSBOTTOM, FOCUSLEFT, FOCUSTOP, self.get_box());
        else:
            display_list.drawfbox(PARCOLOR, self.get_box())
            display_list.draw3dbox(FOCUSLEFT, FOCUSTOP, FOCUSRIGHT, FOCUSBOTTOM, self.get_box());
        VerticalWidget.draw(self, display_list)

class ExclWidget(VerticalWidget):
    def draw(self, display_list):
        if self.selected:
            display_list.drawfbox(self.highlight(EXCLCOLOR), self.get_box())
            display_list.draw3dbox(FOCUSRIGHT, FOCUSBOTTOM, FOCUSLEFT, FOCUSTOP, self.get_box());
        else:
            display_list.drawfbox(EXCLCOLOR, self.get_box())
            display_list.draw3dbox(FOCUSLEFT, FOCUSTOP, FOCUSRIGHT, FOCUSBOTTOM, self.get_box());
        VerticalWidget.draw(self, display_list)

class PrioWidget(VerticalWidget):
    def draw(self, display_list):
        if self.selected:
            display_list.drawfbox(self.highlight(PRIOCOLOR), self.get_box())
            display_list.draw3dbox(FOCUSRIGHT, FOCUSBOTTOM, FOCUSLEFT, FOCUSTOP, self.get_box());
        else:
            display_list.drawfbox(PRIOCOLOR, self.get_box())
            display_list.draw3dbox(FOCUSLEFT, FOCUSTOP, FOCUSRIGHT, FOCUSBOTTOM, self.get_box());
        VerticalWidget.draw(self, display_list)

class SwitchWidget(VerticalWidget):
    def draw(self, display_list):
        if self.selected:
            display_list.drawfbox(self.highlight(ALTCOLOR), self.get_box())
            display_list.draw3dbox(FOCUSRIGHT, FOCUSBOTTOM, FOCUSLEFT, FOCUSTOP, self.get_box());
        else:
            display_list.drawfbox(ALTCOLOR, self.get_box());
            display_list.draw3dbox(FOCUSLEFT, FOCUSTOP, FOCUSRIGHT, FOCUSBOTTOM, self.get_box());
        VerticalWidget.draw(self, display_list);

##############################################################################
# The Media objects (images, videos etc) in the Structure view.

class MediaWidget(MMNodeWidget):
    # A view of an object which is a playable media type.
    # NOT the structure nodes.

    # TODO: this has some common code with the two functions above - should they
    # have a common ancester?

    # TODO: This class can be broken down into various different node types (img, video)
    # if the drawing code is different enough to warrent this.
    
    def __init__(self, node, root):
        MMNodeWidget.__init__(self, node, root)
        self.transition_in = TransitionWidget(self, root, 'in')
        self.transition_out = TransitionWidget(self, root, 'out')

        self.pushbackbar = PushBackBarWidget(root);
        self.pushbackbar.parent = self; # The pushbackbar refers to values from self.
        self.downloadtime = 0.0;        # Distance to draw - MEASURED IN PIXELS
        self.downloadtime_lag = 0.0;    # Distance to push this node to the right - MEASURED IN PIXELS.
        self.compute_download_time();
        
    def destroy(self):
        # Remove myself from the MMNode view{} dict.
        MMNodeWidget.destroy(self)

    def is_hit(self, pos):
        return self.transition_in.is_hit(pos) or self.transition_out.is_hit(pos) or MMNodeWidget.is_hit(self, pos);

    def compute_download_time(self):
        # Compute the download time for this widget.
        # Values are in distances (self.downloadtime is a distance).
         
        # First get available bandwidth. Silly algorithm to be replaced sometime: in each par we evenly
        # divide the available bandwidth, for other structure nodes each child has the whole bandwidth
        # available.
        availbw  = settings.get('system_bitrate')
        division = 1
        ancestor = self.node.parent
        bwfraction = MMAttrdefs.getattr(self.node, 'project_bandwidth_fraction')
        while ancestor:
            if ancestor.type == 'par':
                # If the child we are coming from has a bandwidth fraction defined
                # we use that, otherwise we divide evenly
                if bwfraction < 0:
                    bwfraction = 1.0 / len(ancestor.children)
                availbw = availbw * bwfraction
            bwfraction = MMAttrdefs.getattr(ancestor, 'project_bandwidth_fraction')
            ancestor = ancestor.parent
        
        # Get amount of data we need to load
        try:
            prearm, bw = Bandwidth.get(self.node, target=1)
        except Bandwidth.Error:
            prearm = 0
        if not prearm:
            prearm = 0
        prearmtime = prearm / availbw
        
        # Now subtract the duration of the previous node: this fraction of
        # the downloadtime is no problem.
        prevnode = self.node.GetPrevious()
        if prevnode:
            prevnode_duration = prevnode.t1-prevnode.t0
        else:
            prevnode_duration = 0
        lagtime = prearmtime - prevnode_duration
        
        # Now convert this from time to distance. 
        node_duration = (self.node.t1-self.node.t0)
        if node_duration <= 0: node_duration = 1
        l,t,r,b = self.pos_rel
        node_width = r-l
        lagwidth = lagtime * node_width / node_duration
 
        self.downloadtime = 0
        self.downloadtime_lag = lagwidth

    def recalc(self):
        l,t,r,b = self.pos_rel
        lag = self.get_relx(self.downloadtime_lag)
        h = self.get_rely(12);          # 12 pixels high.
        self.pushbackbar.moveto((l-lag,t,l,t+h))
#        l = l + self.get_relx(1);
#        b = b - self.get_rely(1);
#        r = r - self.get_relx(1);
        t = t + self.get_rely(sizes_notime.TITLESIZE)
        pix16x = self.get_relx(16);
        pix16y = self.get_rely(16);
        self.transition_in.moveto((l,b-pix16y,l+pix16x, b))
        self.transition_out.moveto((r-pix16x,b-pix16y,r, b))
#        dt = self.get_relx(self.downloadtime)
        MMNodeWidget.recalc(self) # This is probably not necessary.

    def get_minsize(self):
        xsize = self.get_relx(sizes_notime.MINSIZE)
        ysize = self.get_rely(sizes_notime.MINSIZE)
#        ysize = ysize + self.get_rely(sizes_notime.TITLESIZE)
        return xsize, ysize

    def get_minsize_abs(self):
        # return the minimum size of this node, in pixels.
        # Calld to work out the size of the canvas.
        xsize = sizes_notime.MINSIZE
        ysize = sizes_notime.MINSIZE# + sizes_notime.TITLESIZE
        return (xsize, ysize)
    
    def get_maxsize(self):
        return self.get_relx(sizes_notime.MAXSIZE), self.get_rely(sizes_notime.MAXSIZE)

    def draw(self, displist):
        x,y,w,h = self.get_box()     
        y = y + self.get_rely(sizes_notime.TITLESIZE)
        h = h - self.get_rely(sizes_notime.TITLESIZE)
        
        willplay = self.root.showplayability or self.node.WillPlay()
        ntype = self.node.GetType()

        if willplay:
            color = LEAFCOLOR
        else:
            color = LEAFCOLOR_NOPLAY
                        
        if self.selected:
            displist.drawfbox(self.highlight(color), self.get_box())
            displist.draw3dbox(FOCUSRIGHT, FOCUSBOTTOM, FOCUSLEFT, FOCUSTOP, self.get_box())
        else:
            displist.drawfbox(color, self.get_box())
            displist.draw3dbox(FOCUSLEFT, FOCUSTOP, FOCUSRIGHT, FOCUSBOTTOM, self.get_box())            

        # Draw the image.
        image_filename = self.__get_image_filename()
        if image_filename != None:
            box = displist.display_image_from_file(
                self.__get_image_filename(),
                center = 1,
                # The coordinates should all be floating point numbers.
                coordinates = (x+w/12, y+h/6, 5*(w/6), 4*(h/6)),
                scale = -2
                )
            displist.fgcolor(TEXTCOLOR)
            displist.drawbox(box)

        # Draw the name
        displist.fgcolor(CTEXTCOLOR)
        displist.usefont(f_title)
        l,t,r,b = self.pos_rel
        b = t+self.get_rely(sizes_notime.TITLESIZE) + self.get_rely(sizes_notime.VEDGSIZE)
#        l = l + self.get_relx(16)       # Maybe have an icon there soon.
        displist.centerstring(l,t,r,b,self.name)

        # Draw the silly transitions.
        if self.root.transboxes:
            self.transition_in.draw(displist)
            self.transition_out.draw(displist)
        

    def __get_image_filename(self):
        # I just copied this.. I don't know what it does. -mjvdg.
        f = None
        
        url = self.node.GetAttrDef('file', None)
        if url:
            media_type = MMmimetypes.guess_type(url)[0]
        else:
            #print "DEBUG: get_image_filename : url is None."
            return None
        
        channel_type = self.node.GetChannelType()
#        if channel_type == 'sound' or channel_type == 'video':
            # TODO: return a sound or video bitmap.
#            print "DEBUG: get_image_filename: url is a sound or video."
 #           return None
        if url and self.root.thumbnails and channel_type == 'image':
            url = self.node.context.findurl(url)
            try:
                f = MMurl.urlretrieve(url)[0]
            except IOError, arg:
#                print "DEBUG: Could not load image!"
                self.root.set_infoicon('error', 'Cannot load image: %s'%`arg`)
        else:
            f = os.path.join(self.root.datadir, '%s.tiff'%channel_type)
#        print "DEBUG: f is ", f
        return f

    def get_obj_at(self, pos):
        if self.is_hit(pos):
            if self.transition_in.is_hit(pos):
                return self.transition_in
            elif self.transition_out.is_hit(pos):
                return self.transition_out
            else:
                return self
        else:
            return None
class TransitionWidget(MMNodeWidget):
    # This is a box at the bottom of a node that represents the in or out transition.
    def __init__(self, parent, root, inorout):
        self.in_or_out = inorout
        MMNodeWidget.__init__(self, parent.node, root)
        self.parent = parent

    def select(self):
        # XXXX Note: this code assumes the select() is done on mousedown, and
        # that we can still post a menu at this time.
        self.parent.select()
        self.posttransitionmenu()

    def unselect(self):
        self.parent.unselect()
    
    def draw(self, displist):
        if self.in_or_out is 'in':
            displist.drawicon(self.get_box(), 'transin')
        else:
            displist.drawicon(self.get_box(), 'transout')

    def attrcall(self):
        self.root.toplevel.setwaiting()
        import AttrEdit
        if self.in_or_out is 'in':
            AttrEdit.showattreditor(self.root.toplevel, self.node, 'transIn')
        else:
            AttrEdit.showattreditor(self.root.toplevel, self.node, 'transOut')

    def posttransitionmenu(self):
        transitionnames = self.node.context.transitions.keys()
        transitionnames.sort()
        transitionnames.insert(0, 'No transition')
        if self.in_or_out == 'in':
            which = 'transIn'
        else:
            which = 'transOut'
        curtransition = MMAttrdefs.getattr(self.node, which)
        if not curtransition:
            curtransition = 'No Transition'
        if curtransition in transitionnames:
            transitionnames.remove(curtransition)
        transitionnames.insert(0, curtransition)
        # XXXX Post menu and interact
        print 'CURTRANS', curtransition, 'LIST', transitionnames
        new = curtransition # XXXX Get from menu selection
        if new == curtransition:
            return
        if new == 'No transition':
            new = ''
        editmgr = self.root.context.editmgr
        if not editmgr.transaction():
            return # Not possible at this time
        editmgr.setnodeattr(self.node, which, new)
        editmgr.commit()
 
class PushBackBarWidget(Widgets.Widget):
    # This is a push-back bar between nodes.
    def draw(self, displist):
        # TODO: draw color based on something??
        displist.fgcolor(TEXTCOLOR)
        displist.drawfbox(COLCOLOR, self.get_box())
        displist.drawbox(self.get_box())

    def drawselected(self, displist):
        displist.fgcolor(TEXTCOLOR)
        displist.drawfbox(COLCOLOR, self.get_box())
        displist.drawbox(self.get_box())

    def select(self):
        self.parent.select()

class CollapseButtonWidget(Widgets.Widget):
    # This is the "expand/collapse" button at the right hand corner of the nodes.
    def __init__(self, parent, root):
        Widgets.Widget.__init__(self, root);
        self.parent=parent;

    def recalc(self):
        l,t,w,h = self.parent.get_box();
        l=l+self.get_relx(1)            # Trial-and-error numbers.
        t = t+self.get_rely(2)
        r = l + self.get_relx(10);      # This is pretty bad code..
        b = t+self.get_rely(10);
        self.moveto((l,t,r,b));
            
    def draw(self, displist):
        pass;                           # Disabled for the meanwhile.
        if self.parent.collapsed:
            displist.drawicon(self.get_box(), 'closed')
        else:
            displist.drawicon(self.get_box(), 'open')
        
