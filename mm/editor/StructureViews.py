# These are the standard views for a structure.

# TODO: rename everything to "widgets"

import Interactive;
import MMurl, MMAttrdefs, MMmimetypes
from AppDefaults import *

def create_MMNode_view(node, root):
    assert root != None;
    ntype = node.GetType();
    if ntype == 'seq':
        return SeqWidget(node, root);
    elif ntype == 'par':
        return ParWidget(node, root);
    elif ntype == 'alt':
        return ExclWidget(node, root);
    elif ntype == 'ext':
        return MediaWidget(node, root);
    # TODO: test for a realmedia MMslide node.
    elif ntype == 'imm':
#        print "TODO: Got an imm node.";
        return MediaWidget(node, root);
    else:
        print "DEBUG: Error! I am not sure what sort of node this is!! StructureViews.py:12";
        print "Node appears to be a ", ntype;
        return None;

class MMNodeWidget(Interactive.Interactive):
    # View of a Node within the Hierarchy view
    def __init__(self, node, root):
        Interactive.Interactive.__init__(self, root);
        self.node = node;               # : MMNode
        self.node.views['struct_view'] = self;
        
    def destroy(self):
        # Prevent cyclic dependancies.
        Interactive.Interactive.destroy(self);
        del self.node.views['struct_view'];
        self.node = None;
        
    #
    # Menu handling functions, aka callbacks.
    #

##	def helpcall(self):
##		import Help
##		Help.givehelp('Hierarchy_view')

    def expandcall(self):
        # 'Expand' the view of this node.
        assert 0;
        self.root.toplevel.setwaiting()
        if hasattr(self.node, 'expanded'):
            collapsenode(self.node)
        else:
            expandnode(self.node)
        self.root.recalc()

    def expandallcall(self, expand):
        # Expand the view of this node and all kids.
        assert 0;
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
    # TODO: make this inherit only from Interactive.Interactive and aggregate a list.
    # A view of a seq, par, excl or something else that might exist.
    def __init__(self, node, root):
        MMNodeWidget.__init__(self, node, root);
        # Create more nodes under me if there are any.
        self.children = [];
        for i in self.node.children:
            bob = create_MMNode_view(i, root);
            if bob == None:
                print "TODO: you haven't written all the code yet, have you Mike?";
            else:
                self.children.append(bob);

    def destroy(self):
        MMNodeWidget.destroy(self);
        self.children = None;

    def get_obj_at(self, pos):
        # Return the MMNode widget at position x,y
        # Oh, how I love recursive methods :-). Nice. -mjvdg.
        if self.is_hit(pos):
            for i in self.children:
                ob = i.get_obj_at(pos)
                if ob != None:
                    return ob;
            return self;
        else:
            return None;

    def draw(self, displist):
        # This is a base class for other classes.. this code only gets
        # called once the aggregating node has been called.
        # Draw only the children.
        print "DEBUG: draw: length of children: ", len(self.children);
        for i in self.children:
            i.draw(displist);

class SeqWidget(StructureObjWidget):
    def draw(self, display_list):
        if self.selected: 
            display_list.drawfbox(self.highlight(SEQCOLOR), self.get_box())
        else:
            display_list.drawfbox(SEQCOLOR, self.get_box());

        display_list.fgcolor(TEXTCOLOR);
        display_list.drawbox(self.get_box());
        StructureObjWidget.draw(self, display_list);

    def get_minsize(self):
        # Return the minimum size that I can be.
        min_width = 0.0; min_height = 0.0;

        print "DEBUG: get_minsize: length of children is: ", len(self.children), self;

        for i in self.children:
            w, h = i.get_minsize();
            assert w < 1.0 and w > 0.0;
            assert h < 1.0 and h > 0.0;
            min_width = min_width + w;
            if h > min_height:
                min_height = h;
        xgap = self.get_relx(sizes_notime.GAPSIZE);

        assert min_width < 1.0;
        assert min_height < 1.0;

        #             current +   gaps between nodes  +  gaps at either end      
        min_width = min_width + xgap*( len(self.children) - 1) + 2*self.get_relx(sizes_notime.HEDGSIZE);
        min_height = min_height + 2 *self.get_rely(sizes_notime.VEDGSIZE);
        return min_width, min_height;

    def get_minsize_abs(self):
        # Everything here calculated in pixels.
        mw=0; mh=0;
        print "DEBUG: get_minsize_abs: length of children is: ", len(self.children)
        for i in self.children:
            assert isinstance(i, MMNodeWidget);
            w,h = i.get_minsize_abs();
            if h > mh: mh=h;
            mw = mw + w;
        mw = mw + sizes_notime.GAPSIZE*(len(self.children)-1) + 2*sizes_notime.HEDGSIZE;
        mh = mh + 2*sizes_notime.VEDGSIZE;
        return mw, mh;
        
    def recalc(self):
        # Untested.
        # Recalculate the position of all the contained boxes.
        # Algorithm: Iterate through each of the MMNodes children's views and find their minsizes.
        # Apportion free space equally, based on the size of self.
        # TODO: This does not test for maxheight();
        
        l, t, r, b = self.pos_rel;
        min_width, min_height = self.get_minsize();

        free_width = (r-l) - min_width;
        if free_width < 0.0:
            print "Warning! free_width is less than 0.0!"
            free_width = 0.0;

        l = float(l) + self.get_relx(sizes_notime.HEDGSIZE);
        t = float(t) + self.get_rely(sizes_notime.VEDGSIZE);

        b = float(b) - self.get_rely(sizes_notime.VEDGSIZE);

        for medianode in self.children:    # for each MMNode:
            w,h = medianode.get_minsize();
            if h > (b-t):               # If the node needs to be bigger than the available space...
                print "Error: Node is too big!";
#                assert 0;               # This shouldn't happen because the minimum size of this node
                                        # has already been determined to be bigger than this in minsize()
            # Take a portion of the free available width, fairly.
            if free_width == 0.0:
                thisnode_free_width = 0.0;
            else:
                thisnode_free_width = (float(w) / min_width) * free_width;
            # Give the node the free width.
            r = l + w + thisnode_free_width + self.get_relx(sizes_notime.HEDGSIZE);
            
#            print "DEBUG: Repositioning node to ", l, t, r, b;
            if r > 1.0:
#                print "ERROR!!! Node extends too far right.. clipping..";
                r = 1.0;
            if b > 1.0:
#                print "ERROR!! Node extends too far down.. clipping..";
                b = 1.0;
            if l > 1.0:
#                print "ERROR!! Node starts too far across.. clipping..";
                l = 1.0;
                r = 1.0;

            medianode.moveto((l,t,r,b));
            medianode.recalc();
            l = r + self.get_relx(sizes_notime.GAPSIZE);
        
        
class ParWidget(StructureObjWidget):
    def draw(self, display_list):
        if self.selected:
            display_list.drawfbox(self.highlight(PARCOLOR), self.get_box());
        else:
            display_list.drawfbox(PARCOLOR, self.get_box());
        display_list.fgcolor(TEXTCOLOR);
        display_list.drawbox(self.get_box());
        StructureObjWidget.draw(self, display_list);

    def get_minsize(self):
        # Return the minimum size that I can be.
        min_width = 0; min_height = 0;

        for i in self.children:
            w, h = i.get_minsize();
            assert w < 1.0 and w > 0.0;
            assert h < 1.0 and h > 0.0;
            if w > min_width:           # The width is the greatest of the width of all children.
                min_width = w;
            min_height = min_height + h;

        ygap = self.get_rely(sizes_notime.GAPSIZE);

        assert min_width < 1.0;
        assert min_height < 1.0;

        min_width = min_width + 2*self.get_relx(sizes_notime.HEDGSIZE);
        min_height = min_height + ygap*(len(self.children)-1) + 2.0*self.get_rely(sizes_notime.VEDGSIZE);

        assert min_width < 1.0 and min_width > 0.0;
        assert min_height < 1.0 and min_height > 0.0;

        return min_width, min_height;

    def get_minsize_abs(self):
        mw=0; mh=0;

        for i in self.children:
            w,h = i.get_minsize_abs();
            if w > mw: mw=w;
            mh=mh+h;
        mh = mh + sizes_notime.GAPSIZE*(len(self.children)-1) + 2*sizes_notime.VEDGSIZE;
        mw = mw + 2*sizes_notime.VEDGSIZE;
        return mw, mh;

    def recalc(self):
        # Untested.
        # Recalculate the position of all the contained boxes.
        # Algorithm: Iterate through each of the MMNodes children's views and find their minsizes.
        # Apportion free space equally, based on the size of self.
        # TODO: This does not test for maxheight();
        
        l, t, r, b = self.pos_rel;
        min_width, min_height = self.get_minsize();
        free_height = (t-b) - min_height;
        if free_height < 0.0 or free_height > 1.0:
#            print "Warning! free_width is less than 0.0!"
            free_height = 0.0;

        l = float(l) + self.get_relx(sizes_notime.HEDGSIZE);
        r = float(r) - self.get_relx(sizes_notime.HEDGSIZE);
        t = float(t) + self.get_rely(sizes_notime.VEDGSIZE);
        

        for medianode in self.children:    # for each MMNode:
            w,h = medianode.get_minsize();
            if h > (b-t):               # If the node needs to be bigger than the available space...
                pass;                   # TODO!!!!!
#                print "Error: Node is too big!";
#                assert 0;               # This shouldn't happen because the minimum size of this node
                                        # has already been determined to be bigger than this in minsize()
            # Take a portion of the free available width, fairly.
            if free_height == 0.0:
#                print "Parview.recalc: Warning! Node has no free height.";
                thisnode_free_height = 0.0;
            else:
                thisnode_free_height = (float(h)/min_height) * free_height;
            # Give the node the free width.
            b = t + h + self.get_rely(sizes_notime.GAPSIZE) + thisnode_free_height ;
            # r = l + w; # Wrap the node to it's minimum size.

            if r > 1.0:
#                print "ERROR!!! Node extends too far right.. clipping..";
                r = 1.0;
            if b > 1.0:
#                print "ERROR!! Node extends too far down.. clipping..";
                b = 1.0;
            if l > 1.0:
#                print "ERROR!! Node starts too far across.. clipping..";
                l = 1.0;
                r = 1.0;
                
            medianode.moveto((l,t,r,b));
            medianode.recalc();
            t = b + self.get_rely(sizes_notime.GAPSIZE);


class ExclWidget(StructureObjWidget):
    pass;


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
        MMNodeWidget.__init__(self, node, root);
        self.transition_in = TransitionWidget(root, 'in');
        self.transition_out = TransitionWidget(root, 'out');

    def destroy(self):
        # Remove myself from the MMNode view{} dict.
        MMNodeWidget.destroy(self);

    def recalc(self):
        l,t,r,b = self.pos_rel;
        self.transition_in.moveto((l,b-(1.0/6.0)*(b-t),l+(r-l)*(1.0/6.0),b));
        self.transition_out.moveto((l+(5.0/6.0)*(r-l),b-(1.0/6.0)*(b-t),r,b));
        MMNodeWidget.recalc(self); # This is probably not necessary.

    def get_minsize(self):
        return self.get_relx(sizes_notime.MINSIZE), self.get_rely(sizes_notime.MINSIZE);

    def get_maxsize(self):
        return self.get_relx(sizes_notime.MAXSIZE), self.get_rely(sizes_notime.MAXSIZE);

    def draw(self, displist):
        print "MediaWidget.draw selected=", self.selected;
        x,y,w,h = self.get_box();     
        
        willplay = self.root.showplayability or self.node.WillPlay();
        ntype = self.node.GetType();

        if willplay:
            color = LEAFCOLOR;
        else:
            color = LEAFCOLOR_NOPLAY;
                        
        if self.selected:
            displist.drawfbox(self.highlight(color), self.get_box());
        else:
            displist.drawfbox(color, self.get_box());
        displist.fgcolor(TEXTCOLOR);
        displist.drawbox(self.get_box());

        # Draw the image.
        image_filename = self.__get_image_filename();
        if image_filename != None:
            box = displist.display_image_from_file(
                self.__get_image_filename(),
                center = 1,
                # The coordinates should all be floating point numbers.
                coordinates = (x+w/6, y+h/6, 4*(w/6), 4*(h/6)),
                scale = -2
                );
            displist.fgcolor(TEXTCOLOR);
            displist.drawbox(box);

        # Draw the silly transitions.
        self.transition_in.draw(displist);
        self.transition_out.draw(displist);
        

    def __get_image_filename(self):
        # I just copied this.. I don't know what it does. -mjvdg.
        
        url = self.node.GetAttrDef('file', None);

        if url:
            media_type = MMmimetypes.guess_type(url)[0];
        else:
#            print "DEBUG: get_image_filename : url is None.";
            return None;

        channel_type = self.node.GetChannelType();
        if channel_type == 'sound' or channel_type == 'video':
            # TODO: return a sound or video bitmap.
#            print "DEBUG: get_image_filename: url is a sound or video.";
            return None;
        elif url and self.root.thumbnails and channel_type == 'image':
            url = self.node.context.findurl(url);
            try:
                f = MMurl.urlretrieve(url)[0];
            except IOError, arg:
                print "DEBUG: Could not load image!";
                self.root.set_infoicon('error', 'Cannot load image: %s'%`arg`);
        return f;

    def get_obj_at(self, pos):
        if self.is_hit(pos):
            return self;
        else:
            return None;

    def get_minsize_abs(self):
        # return the minimum size of this node, in pixels.
        # Calld to work out the size of the canvas.
        return (sizes_notime.MINSIZE, sizes_notime.MINSIZE);
    

class TransitionWidget(Interactive.Interactive):
    # TODO: implement and use the append functionality of the Interactive class.

    def __init__(self, root, inorout):
        self.in_or_out = inorout;
        Interactive.Interactive.__init__(self, root);
    
    def draw(self, displist):
        displist.drawfbox((255,255,255), self.get_box());
        displist.drawbox(self.get_box());
