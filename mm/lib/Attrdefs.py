mtime = 902312797
Attrdefs = {'align': (('string', None),
           'left',
           'Alignment',
           'default',
           'Alignment of short datasets',
           'channel'),
 'anchorlist': (('list',
                 ('enclosed',
                  ('tuple',
                   [('any', None),
                    ('int', None),
                    ('enclosed', ('list', ('any', None)))]))),
                [],
                'Anchors',
                'hidden',
                'List of anchors on this node',
                'raw'),
 'arm_duration': (('float', None),
                  -1.0,
                  'Arm duration',
                  'hidden',
                  'Time needed to arm this event before displaying',
                  'raw'),
 'axis': (('tuple', [('float', None), ('float', None)]),
          (-1.0, -1.0),
          'Axis',
          'default',
          'Draw axis if >0, specifies tick-interval',
          'channel'),
 'bag_index': (('name', None),
               'undefined',
               'Choice index',
               'childnodename',
               'Name of child auto-started when choice node plays',
               'normal'),
 'base_window': (('name', None),
                 'undefined',
                 'Channel base window',
                 'basechannelname',
                 'Name of window in which channelwin is created',
                 'raw'),
 'base_winoff': (('tuple',
                  [('float', None),
                   ('float', None),
                   ('float', None),
                   ('float', None)]),
                 (0.0, 0.0, 1.0, 1.0),
                 'Border offset',
                 'default',
                 'Position/size in percent of base window',
                 'channel'),
 'bgcolor': (('tuple', [('int', None), ('int', None), ('int', None)]),
             (255, 255, 255),
             'Background color',
             'color',
             'Color used for text/images in window',
             'channel'),
 'bgimg': (('string', None),
           '',
           'Background image',
           'file',
           'Background image for window',
           'channel'),
 'border': (('int', None),
            1,
            'Channel border',
            'default',
            'Determines whether channel window has a border (1=yes)',
            'raw'),
 'bucolor': (('tuple', [('int', None), ('int', None), ('int', None)]),
             (255, 0, 0),
             'Button color',
             'color',
             'Color used for anchors in window',
             'channel'),
 'center': (('bool', None),
            1,
            'Center image',
            'default',
            'Determines whether image is centered',
            'channel'),
 'channel': (('name', None),
             'undefined',
             'Channel',
             'channelname',
             'Name of channel used to render this node/subtree',
             'inherited'),
 'channellist': (('list',
                  ('enclosed',
                   ('tuple', [('name', None), ('attrdict', None)]))),
                 [],
                 'Channel List',
                 'hidden',
                 'Channels used in this document (root node only)',
                 'normal'),
 'clipbegin': (('string', None),
               '',
               'Clip begin',
               'default',
               'Start of range of frames to be played',
               'channel'),
 'clipend': (('string', None),
             '',
             'Clip end',
             'default',
             'End of range of frames to be played',
             'channel'),
 'comment': (('string', None),
             '',
             'Comment',
             'default',
             'An arbitrary comment string, not interpreted',
             'raw'),
 'crop': (('tuple',
           [('float', None),
            ('float', None),
            ('float', None),
            ('float', None)]),
          (0.0, 0.0, 0.0, 0.0),
          'Image crop',
          'default',
          'Crop image.  Values are fractions to crop from top, bottom, left, right.',
          'channel'),
 'cview_winpos': (('tuple', [('float', None), ('float', None)]),
                  (-1.0, -1.0),
                  'Time chart winpos',
                  'hidden',
                  'Window position for Time chart view',
                  'raw'),
 'cview_winsize': (('tuple', [('float', None), ('float', None)]),
                   (115.234375, 115.234375),
                   'Time chart winsize',
                   'hidden',
                   'Window size for Time chart view',
                   'raw'),
 'drawbox': (('bool', None),
             1,
             'Draw anchor boxes',
             'default',
             'Draw anchors as boxes',
             'channel'),
 'duration': (('float', None),
              0.0,
              'Duration',
              'default',
              'Duration of a node/subtree (in seconds)',
              'normal'),
 'fgcolor': (('tuple', [('int', None), ('int', None), ('int', None)]),
             (0, 0, 0),
             'Foreground color',
             'color',
             'Color used for background of window',
             'channel'),
 'file': (('string', None),
          '/dev/null',
          'File',
          'file',
          'File name for external node',
          'channel'),
 'font': (('string', None),
          'Times-Roman',
          'Font',
          'font',
          'Font used to display text',
          'channel'),
 'gtype': (('string', None),
           'line',
           'Graphtype',
           'default',
           'Type of graph: bar, line, hline',
           'channel'),
 'hicolor': (('tuple', [('int', None), ('int', None), ('int', None)]),
             (255, 0, 0),
             'Hilight color',
             'color',
             'Color used for highlighted anchors in window',
             'channel'),
 'hview_winpos': (('tuple', [('float', None), ('float', None)]),
                  (-1.0, -1.0),
                  'Hierarchy winpos',
                  'hidden',
                  'Window position for hierarchy view',
                  'raw'),
 'hview_winsize': (('tuple', [('float', None), ('float', None)]),
                   (115.234375, 115.234375),
                   'Hierarchy winsize',
                   'hidden',
                   'Window size for hierarchy view',
                   'raw'),
 'hyperlinks': (('list',
                 ('enclosed',
                  ('tuple',
                   [('enclosed',
                     ('tuple', [('string', None), ('any', None)])),
                    ('enclosed',
                     ('tuple', [('string', None), ('any', None)])),
                    ('int', None),
                    ('int', None)]))),
                [],
                'Hyperlink list',
                'hidden',
                'Hyperlinks within this document (root node only)',
                'raw'),
 'links_winpos': (('tuple', [('float', None), ('float', None)]),
                  (-1.0, -1.0),
                  'Link edit window position',
                  'hidden',
                  'Position of link edit window',
                  'raw'),
 'links_winsize': (('tuple', [('float', None), ('float', None)]),
                   (146.923828125, 132.51953125),
                   'Link edit window size',
                   'hidden',
                   'Size of link edit window',
                   'raw'),
 'loop': (('int', None),
          1,
          'Loop',
          'default',
          'Number of times the node should loop (0 is infinite)',
          'raw'),
 'macprog': (('string', None),
             '',
             'Mac program signature',
             'default',
             '4-byte application signature (mac only)',
             'channel'),
 'mcgroup': (('string', None),
             '',
             'Multicast group',
             'default',
             'IP Multicast group address to listen to',
             'raw'),
 'mcttl': (('int', None),
           3,
           'Multicast TTL',
           'default',
           'TTL for outgoing multicast messages',
           'raw'),
 'mimetype': (('string', None),
              '',
              'MIME type',
              'default',
              'MIME type of media object',
              'raw'),
 'name': (('name', None),
          '',
          'Node name',
          'default',
          'Name given to a node',
          'raw'),
 'noanchors': (('bool', None),
               0,
               'Ignore anchors',
               'default',
               'Ignore anchors and other HTML tags',
               'channel'),
 'nonlocal': (('bool', None),
              0,
              'Remote only',
              'default',
              'Ignore incoming messages from local machine',
              'raw'),
 'player_winpos': (('tuple', [('float', None), ('float', None)]),
                   (-1.0, -1.0),
                   'Player winpos',
                   'hidden',
                   'Window position for player control panel',
                   'raw'),
 'player_winsize': (('tuple', [('float', None), ('float', None)]),
                    (83.544921875, 46.09375),
                    'Player winsize',
                    'hidden',
                    'Window size for player control panel',
                    'raw'),
 'pointsize': (('float', None),
               0.0,
               'Point size',
               'default',
               'Point size of text displayed in window',
               'channel'),
 'popup': (('bool', None),
           1,
           'Popup on play',
           'default',
           'Determines whether channel pops up upon playing a node',
           'raw'),
 'port': (('int', None),
          7000,
          'UDP port',
          'default',
          'UDP port for external hyperjumps',
          'raw'),
 'queuesize': (('float', None),
               0.0,
               'Queue size',
               'default',
               'Audio playback queue size',
               'channel'),
 'scale': (('float', None),
           0.0,
           'Scale factor',
           'default',
           'Image magnification (0.0 means fit in window)',
           'channel'),
 'scalefilter': (('name', None),
                 '',
                 'Scaling filter',
                 'default',
                 'Name of filter used after image scaling',
                 'channel'),
 'style': (('list', ('name', None)),
           [],
           'Style(s)',
           'default',
           'List of style names that apply to this node/subtree',
           'raw'),
 'style_winpos': (('tuple', [('float', None), ('float', None)]),
                  (-1.0, -1.0),
                  'Style editor winpos',
                  'hidden',
                  'Window position for style editor',
                  'raw'),
 'style_winsize': (('tuple', [('float', None), ('float', None)]),
                   (86.42578125, 92.1875),
                   'Style editor winsize',
                   'hidden',
                   'Window size for style editor',
                   'raw'),
 'styledict': (('namedict', ('attrdict', None)),
               {},
               'Style Dictionary',
               'hidden',
               'Styles used in this document (root node only)',
               'normal'),
 'synctolist': (('list',
                 ('enclosed',
                  ('tuple',
                   [('uid', None),
                    ('bool', None),
                    ('float', None),
                    ('bool', None)]))),
                [],
                'SyncTo list',
                'hidden',
                'List of sync arcs ending at this node',
                'raw'),
 'system_bitrate': (('int', None),
                    0,
                    'System bitrate',
                    'default',
                    'System bitrate',
                    'raw'),
 'system_captions': (('bool', None),
                     0,
                     'System captions',
                     'default',
                     'System captions',
                     'raw'),
 'system_language': (('string', None),
                     '',
                     'System language',
                     'default',
                     'System language',
                     'raw'),
 'system_overdub_or_caption': (('string', None),
                               '',
                               'System overdub or caption',
                               'default',
                               'System overdub or caption',
                               'raw'),
 'system_required': (('string', None),
                     '',
                     'System required',
                     'default',
                     'System required',
                     'raw'),
 'system_screen_depth': (('int', None),
                         0,
                         'System screen depth',
                         'default',
                         'System screen depth',
                         'raw'),
 'system_screen_size': (('tuple', [('int', None), ('int', None)]),
                        (0, 0),
                        'System screen size',
                        'default',
                        'System screen size',
                        'raw'),
 'terminator': (('name', None),
                'LAST',
                'Terminator child',
                'termnodename',
                'Name of child that terminates parallel node',
                'normal'),
 'textalign': (('string', None),
               'center',
               'Alignment',
               'default',
               'Alignment of text in window',
               'channel'),
 'toplevel_winpos': (('tuple', [('float', None), ('float', None)]),
                     (-1.0, -1.0),
                     'Top level winpos',
                     'hidden',
                     'Window position for top level menu',
                     'raw'),
 'toplevel_winsize': (('tuple', [('float', None), ('float', None)]),
                      (31.689453125, 72.021484375),
                      'Top level winsize',
                      'hidden',
                      'Window size for top level menu',
                      'raw'),
 'transparent': (('int', None),
                 0,
                 'Transparent',
                 'transparency',
                 'Determines transparency of window',
                 'raw'),
 'type': (('name', None),
          'null',
          'Channel type',
          'channeltype',
          'Channel type (channel dictionary only)',
          'raw'),
 'units': (('int', None),
           0,
           'Units',
           'units',
           'Units for top-level windows',
           'raw'),
 'unixprog': (('string', None),
              '',
              'Unix program name',
              'default',
              'Application name (unix only)',
              'channel'),
 'video': (('bool', None),
           0,
           'Video output',
           'default',
           'Do image smoothing for video output',
           'channel'),
 'visible': (('bool', None),
             1,
             'Channel visibility',
             'default',
             'Determines visibility of channel',
             'raw'),
 'wanturl': (('bool', None),
             0,
             'Pass URL',
             'default',
             'Pass URL to program (otherwise pass filename)',
             'channel'),
 'winpos': (('tuple', [('float', None), ('float', None)]),
            (-1.0, -1.0),
            'Window position',
            'hidden',
            'Initial window position (x, y) (x axis pointing down!)',
            'raw'),
 'winprog': (('string', None),
             '',
             'Windows program name',
             'default',
             'Application name (windows only)',
             'channel'),
 'winsize': (('tuple', [('float', None), ('float', None)]),
             (0.0, 0.0),
             'Window size',
             'hidden',
             'Initial window size (width, height)',
             'raw'),
 'z': (('int', None), 0, 'Z order', 'default', 'Z order', 'normal')}
