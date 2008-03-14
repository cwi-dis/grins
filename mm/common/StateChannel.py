__version__ = "$Id$"

from Channel import *
import MMState

class StateChannel(Channel):
    node_attrs = Channel.node_attrs + ['ref', 'value']

    def do_play(self, node, curtime):
        stag = node.attrdict['stag']
        if stag == 'setvalue':
            ref = node.GetAttr('state_ref')
            value = node.GetAttr('state_value')
            try:
                n = node.context.state.setvalue(ref, value)
            except MMState.error, e:
                self.errormsg(node, e)
            else:
                self.event((None, 'state', n), curtime)
        elif stag == 'newvalue':
            ref = node.GetAttr('state_ref')
            where = node.GetAttrDef('state_where', 'child')
            name = node.GetAttr('state_name')
            value = node.GetAttr('state_value')
            try:
                n = node.context.state.newvalue(ref, where, name, value)
            except MMState.error, e:
                self.errormsg(node, e)
            else:
                self.event((None, 'state', n), curtime)
        elif stag == 'delvalue':
            ref = node.GetAttr('state_ref')
            try:
                n = node.context.state.delvalue(ref)
            except MMState.error, e:
                self.errormsg(node, e)
            else:
                self.event((None, 'state', n), curtime)
        elif stag == 'send':
            submission = node.attrdict.get('state_submission')
            if not submission:
                return                  # nothing to do
            sdict = node.context.submissions.get(submission)
            if not sdict:
                return                  # nothing to do
            action = sdict.get('action')
            ref = sdict.get('ref')
            method = sdict.get('method')
            replace = sdict.get('replace')
            target = sdict.get('target')
##             if not ref or \
##                    not action or \
##                    method not in ('get', 'post') or \
##                    replace not in ('all', 'instance', 'none'):
##                 return                  # nothing to do
            try:
                node.context.state.send(ref, action, method, replace, target)
            except MMState.error, e:
                self.errormsg(node, e)
