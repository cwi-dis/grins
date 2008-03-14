__version__ = "$Id$"

# This module implements some common treatments between the player version and the editor version
# Currently, all renderers (and create/destroy optimization) are created in this module

# allow to create all renderer before to play.
# For now, don't turn off this flag, it doesn't work for the sound channels
MAKE_RENDERERS_FIRST = 1

# allow to create one renderer by media (without optimization)
ONE_RENDERER_BY_MEDIA_NODE = 0

debug = 0

class PlayerCommon:
    def __init__(self):
        self.nodeToRenderer = {}
        # optimization variables which allow optimizations
        self.__region2RendererList = {}
        self.__pnode2RendererList = {}
        self.__rendererNoreuse = {}
        self.__animateNodeList = []
        self.__iChannelList = []
        self.__tabindex = []
        self.__curentry = None

    def addtabindex(self, tabindex, node, chan):
        import bisect
        inode = (tabindex, node, chan)
        if inode not in self.__tabindex:
            bisect.insort(self.__tabindex, inode)

    def deltabindex(self, tabindex, node, chan):
        entry = (tabindex, node, chan)
        try:
            i = self.__tabindex.index(entry)
        except ValueError:
            # not in list, so nothing to do
            return
        del self.__tabindex[i]
        if self.__curentry == entry:
            chan.anchor_highlight(node, 0)
            if self.__tabindex:
                self.__curentry = self.__tabindex[i % len(self.__tabindex)]
            else:
                self.__curentry = None

    def tab(self):
        if self.__curentry is not None:
            if len(self.__tabindex) == 1:
                return
            i = self.__tabindex.index(self.__curentry) + 1
            tabindex, node, chan = self.__curentry
            chan.anchor_highlight(node, 0)
        elif self.__tabindex:
            i = 0
        else:
            return
        self.__curentry = self.__tabindex[i % len(self.__tabindex)]
        tabindex, node, chan = self.__curentry
        chan.anchor_highlight(node, 1)

    def activate(self):
        if self.__curentry is None:
            return
        tabindex, node, chan = self.__curentry
        chan.onclick(node)

    def clearRendererChannels(self):
        # kill all renderers
        for node, renderer in self.nodeToRenderer.items():
            self.killRenderer(renderer._name)
        self.nodeToRenderer = {}

        # optimization variables which allow optimizations
        self.__region2RendererList = {}
        self.__pnode2RendererList = {}
        self.__rendererNoreuse = {}

    def makeRendererChannels(self):
        if MAKE_RENDERERS_FIRST:
            # update in the same time the animate node list for optimization purpose
            self.__animateList = []
            self.__stateList = []
            nodeList = self.root.GetAllMediaNodes(animateList = self.__animateList, stateList = self.__stateList)
            for node in nodeList:
                renderer = self.getRenderer(node)

    def checkRendererAndIChannels(self):
        self.clearRendererChannels()
        self.clearInternalChannels()
        self.makeRendererChannels()
        self.makeInternalChannels()

    def getRenderer(self, node):
        chan = self.nodeToRenderer.get(node)
        if chan is None:
            # the renderer doesn't exist yet
            if not ONE_RENDERER_BY_MEDIA_NODE:
                chan = self.findRenderer(node)
            else:
                chan = self.makeRenderer(node)
            self.nodeToRenderer[node] = chan

        return chan

    def makeRenderer(self, node):
        ctx = self.context
        regionName = node.GetChannelName()
        chtype = node.GetChannelType()
        chname = self.newChannelName(regionName)
        if debug: print 'make a new renderer : ',chname
        # create just the minimum channel attributes for creating a new channel
        import MMNode
        chan = MMNode.MMChannel(ctx, chname, chtype)
        chan['base_window'] = regionName
        chan['type'] = chtype

        # XXX store in reference document to keep working the player !
        # very bad, but the only way if we don't want change the setlayout method and break something
        ctx.channels.append(chan)
        ctx.channelnames.append(chname)
        ctx.channeldict[chname] = chan

        self.newchannel(chname, chan)
        self.channelnames.append(chname)
        renderer = self.channels[chname]

        return renderer

    def killRenderer(self, name):
        if debug: print 'PlayerCore, killRenderer ',name
        # destroy the relation-ship parent-child before destroying the channel
        ctx = self.context
        try:
            del ctx.channeldict[name]['base_window']
        except:
            print "Unexpected error: PlayerCommon.killRenderer, can't remove ",name
        # XXX remove channel from reference document
        i = ctx.channelnames.index(name)
        del ctx.channels[i]
        del ctx.channelnames[i]
        del ctx.channeldict[name]
        #

        self.killchannel(name)

    def findRenderer(self, node):
        if debug: print 'PlayerCore, findRenderer, for node ',node

        renderer = None
        regionName = node.GetChannelName()
        chtype = node.GetChannelType()
        pnode = node.GetSchedParent()

        # first
        # check if the renderer can be shared
        if (pnode.GetType() == 'seq' and \
                node.GetFill() == 'hold') or \
                node.GetFill() == 'transition':
            noreuse = 1
            if debug: print 'PlayerCore, renderer can''t be shared'
        else:
            noreuse = 0

        # if at this stage, the renderer can't be shared, ignore this section
        if not noreuse:
            if debug: print 'PlayerCore, check for a compatible renderer'
            # second pass
            for ch in self.__region2RendererList.get(regionName, []):
                if ch._attrdict.get('type') == chtype:
                    # found existing renderer of correct type
                    renderer = ch
                    # check whether renderer can be used
                    # we can only use a renderer if it isn't used
                    # by another node parallel/excl to this one
                    parent = pnode
                    while parent is not None:
                        pchanlist = self.__pnode2RendererList.get(parent)
                        if pchanlist != None and pchanlist.has_key(renderer):
                            ptype = parent.GetType()
                            if ptype == 'par':
                                # conflict
                                renderer = None
                                break
                            elif ptype == 'excl':
                                # potential conflict
                                renderer = None
                                break
                            else:
                                # no conflict
                                break
                        parent = parent.GetSchedParent()
                    if renderer is not None:
                        # this renderer can't be reused
                        if self.__rendererNoreuse.get(renderer) is None:
                            if debug: print 'compatible renderer found : ',renderer
                            break
                        else:
                            if debug: print 'compatible renderer found but can''t be reused : ',renderer
                            renderer = None

        # if 'renderer' = None, we haven't found a compatible renderer
        if not renderer or not noreuse:
            renderer = self.makeRenderer(node)
            if noreuse:
                self.__rendererNoreuse[renderer] = 1

            # update local variables
            # allow optimizations
            rdList = self.__region2RendererList.get(regionName)
            if rdList == None:
                rdList = self.__region2RendererList[regionName] = []
            rdList.append(renderer)

            rdList = self.__pnode2RendererList.get(pnode)
            if rdList == None:
                rdList = self.__pnode2RendererList[pnode] = {}
            rdList[renderer] = 1

        if debug: print 'PlayerCore, findRenderer, end renderer=',renderer,' node=',node
        return renderer

    # compute a channel name according to the region name
    def newChannelName(self, regionName):
        # search a new channel name
        name = regionName + ' %d'
        i = 0
        while self.channels.has_key(name % i):
            i = i + 1

        return name     % i

    #
    # Internal channels support (animation support)
    #

    # requirement: makeRendererChannels has to be called before:
    # this method to create __animateList and __stateList
    def makeInternalChannels(self):
        context = self.context
        for node in self.__animateList:
            # for animate par node, we have to manage also dynamicly the right animate nodes
            if node.type == 'animpar':
                from fmtfloat import fmtfloat
                animvals = node.attrdict.get('animvals', [])
                attrs = {}
                for t, v in animvals:
                    if v.has_key('top') and v.has_key('left'):
                        v['pos'] = v['left'], v['top']
                        del v['top'], v['left']
                    attrs.update(v)
                if (attrs.has_key('top') or attrs.has_key('left')) and attrs.has_key('pos'):
                    for t, v in animvals:
                        if v.has_key('pos'):
                            v['left'], v['top'] = v['pos']
                            del v['pos']
                    del attrs['pos']
                attrs = attrs.keys()

                for attr in attrs:
                    if attr == 'selected': # XXX internal value for selected index
                        continue
                    n = context.newnode('animate')
                    self.__animateNodeList.append(n)
                    parent = node.GetParent()
                    parent._addchild(n)
                    n.targetnode = parent
                    n.attrdict['internal'] = 1
#                                       from MMNode import MMSyncArc
#                                       n.attrdict['endlist'] = [MMSyncArc(n, 'end', srcnode = parent, event = 'end', delay = 0)]
                    # to avoid any behavior differences, use the same duration as publish
                    duration = n.targetnode.GetDuration()
                    if duration is not None and duration >= 0:
                        n.attrdict['duration'] = duration
                    times = []
                    vals = []
                    for t, v in animvals:
                        if v.has_key(attr):
                            times.append(t)
                            vals.append(v[attr])
                    n.attrdict['keyTimes'] = times
                    values = []
                    if attr == 'pos':
                        for v in vals:
                            values.append('%d %d' % v)
                        n.attrdict['atag'] = 'animateMotion'
                    elif attr == 'bgcolor':
                        for v in vals:
                            import colors
                            if colors.rcolors.has_key(v):
                                values.append(colors.rcolors[v])
                            else:
                                values.append('#%02x%02x%02x' % v)
                        n.attrdict['atag'] = 'animateColor'
                        n.attrdict['attributeName'] = 'backgroundColor'
                    else:
                        for v in vals:
                            values.append('%d' % v)
                        n.attrdict['atag'] = 'animate'
                        n.attrdict['attributeName'] = attr
                    n.attrdict['values'] = ';'.join(values)

                    # synthesize a name for the channel
                    chname = self.newChannelName('animate%s' % n.GetUID())
                    n.attrdict['channel'] = chname
                    # add to context an internal channel for this node
                    context.addinternalchannels( [(chname, 'animate', n.attrdict), ] )
                    chan = context._ichanneldict[chname]
                    self.__iChannelList.append(chan)
                    self.newichannel(chname, chan)

                # cleanup
                for t, v in animvals:
                    if v.has_key('pos'):
                        v['left'], v['top'] = v['pos']
                        del v['pos']
            else:
                # synthesize a name for the channel
                chname = self.newChannelName('animate%s' % node.GetUID())
                node.attrdict['channel'] = chname
                # add to context an internal channel for this node
                context.addinternalchannels( [(chname, 'animate', node.attrdict), ] )
                chan = context._ichanneldict[chname]
                self.__iChannelList.append(chan)
                self.newichannel(chname, chan)
                # reinitialize the target node
                # please override it!!!
                #node.targetnode = None
        for node in self.__stateList:
            # synthesize a name for the channel
            chname = self.newChannelName('state%s' % node.GetUID())
            node.attrdict['channel'] = chname
            # add to context an internal channel for this node
            context.addinternalchannels([(chname, 'state', node.attrdict)])
            chan = context._ichanneldict[chname]
            self.__iChannelList.append(chan)
            self.newichannel(chname, chan)

    def clearInternalChannels(self):
        # for animate par node, we have to manage also dynamicly the right animate nodes
        for node in self.__animateNodeList:
            node.Extract()
            node.Destroy()
        self.__animateNodeList = []
        for chan in self.__iChannelList:
            self.killichannel(chan.name)
            chan.GetContext()._delinternalchannel(chan.name)
        self.__iChannelList = []
