product grinsed
    id "GRiNS 0.5"
    cutpoint usr/local/grins
    image sw
        id "GRiNS 0.5 Software"
        version 1
        order 9999
        subsys editor default
            id "GRiNS Editor 0.5 Base Software"
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
            id "GRiNS Player 0.5 Base Software"
            replaces self
            replaces grins.sw.player 0 1
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
            id "GRiNS Editor 0.5 Templates"
            replaces self
            prereq (
                grinsed.sw.editor 1 1
            )
            exp grinsed.sw.templates
        endsubsys
    endimage
    image help
        id "GRiNS 0.5 Help Files"
        version 1
        order 9999
        subsys data default
            id "GRiNS Editor 0.5 Tutorial Data"
            replaces self
            prereq (
                grinsed.sw.editor 1 1
            )
            exp grinsed.help.data
        endsubsys
        subsys examples default
            id "GRiNS 0.5 SMIL Examples"
            replaces self
	    replaces grins.help.examples 0 1
            prereq (
                grinsed.sw.editor 1 1
            )
            prereq (
                grinsed.sw.player 1 1
            )
            exp grinsed.help.examples
        endsubsys
        subsys documentation default
            id "GRiNS Editor 0.5 Documentation"
            replaces self
	    replaces grins.help.documentation 0 1
            exp grinsed.help.documentation
        endsubsys
    endimage
    image relnotes
        id "GRiNS 0.5 Release Notes"
        version 1
        order 9999
        subsys relnotes default
            id "GRiNS 0.5 Release Notes"
            replaces self
            replaces grins.relnotes.relnotes 0 1
            exp grinsed.relnotes.relnotes
        endsubsys
    endimage
endproduct
