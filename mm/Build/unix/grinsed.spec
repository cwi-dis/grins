product grinsed
    id "GRiNS 1.0beta"
    cutpoint usr/local/grins
    image sw
        id "GRiNS 1.0beta Software"
        version 1000
        order 9999
        subsys editor default
            id "GRiNS Editor 1.0beta Base Software"
            replaces self
            prereq (
                compiler_eoe.sw.lib 1275056010 maxint
                dmedia_eoe.sw.audio 1275093220 maxint
                dmedia_eoe.sw.lib 1275093220 maxint
                eoe.sw.base 1275093236 maxint
                eoe.sw.gfx 1275093236 maxint
                motif_eoe.sw.eoe 1275093220 maxint
                x_eoe.sw.eoe 1275093220 maxint
            )
            exp grinsed.sw.editor
        endsubsys
        subsys player default
            id "GRiNS Player 1.0beta Base Software"
            replaces self
            replaces grins.sw.player 0 0
            prereq (
                compiler_eoe.sw.lib 1275056010 maxint
                dmedia_eoe.sw.audio 1275093220 maxint
                dmedia_eoe.sw.lib 1275093220 maxint
                eoe.sw.base 1275093236 maxint
                eoe.sw.gfx 1275093236 maxint
                motif_eoe.sw.eoe 1275093220 maxint
                x_eoe.sw.eoe 1275093220 maxint
            )
            exp grinsed.sw.player
        endsubsys
        subsys templates default
            id "GRiNS Editor 1.0beta Templates"
            replaces self
            prereq (
                grinsed.sw.editor 0 0
            )
            exp grinsed.sw.templates
        endsubsys
    endimage
    image help
        id "GRiNS 1.0beta Help Files"
        version 1000
        order 9999
        subsys data default
            id "GRiNS Editor 1.0beta Tutorial Data"
            replaces self
            prereq (
                grinsed.sw.editor 0 0
            )
            exp grinsed.help.data
        endsubsys
        subsys examples default
            id "GRiNS 1.0beta SMIL Examples"
            replaces self
	    replaces grins.help.examples 0 0
            prereq (
                grinsed.sw.editor 0 0
            )
            prereq (
                grinsed.sw.player 0 0
            )
            exp grinsed.help.examples
        endsubsys
        subsys documentation default
            id "GRiNS Editor 1.0beta Documentation"
            replaces self
	    replaces grins.help.documentation 0 0
            exp grinsed.help.documentation
        endsubsys
    endimage
    image relnotes
        id "GRiNS 1.0beta Release Notes"
        version 1000
        order 9999
        subsys relnotes default
            id "GRiNS 1.0beta Release Notes"
            replaces self
            replaces grins.relnotes.relnotes 0 0
            exp grinsed.relnotes.relnotes
        endsubsys
    endimage
endproduct
