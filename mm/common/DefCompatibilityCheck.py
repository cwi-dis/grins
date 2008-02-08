__version__ = "$Id$"

## ##########################################################
## #################### WARNING WARNING WARNING #############
## ##########################################################
# if you modify meta information format about version, you must also modify
# this function (see version.py)

def isCompatibleVersion(versionToCheck):
    try:
        import version, string
        # if information empty, compatible by default
        if versionToCheck == '':
            return 1

        cur_version = version.version.lower()
        cur_list = string.split(cur_version)
        file_version = versionToCheck.lower()
        file_list = string.split(file_version)

        # at first, del 'grins' string for file version
        if len(file_list) > 0 and file_list[0] == 'grins':
            del file_list[0]

        # particular case, try to reconize the first version
        # files creates with first version can be read with all
        if len(file_list) > 1:
            if file_list[0] == 'editor' and file_list[1] == '1.0':
                return 1

        # try to reconize default format
        if len(file_list) < 4:
            return 0

        # retrieve main version qt, g2, ...
        # for realsystem version, normalize the list
        cur_mainversion = cur_list[2]
        if cur_mainversion == 'realsystem':
            cur_mainversion = cur_mainversion+cur_list[3]
            del cur_list[3]
        file_mainversion = file_list[2]
        if file_mainversion == 'realsystem':
            file_mainversion = file_mainversion+file_list[3]
            del file_list[3]

        # if cur main version different of file version, it's not compatible
        if cur_mainversion != file_mainversion:
            return 0

        if len(file_list) < 4:
            return 0

##         # retrieve sub version pro, light, ...
##         cur_subversion = cur_list[0]
##         file_subversion = file_list[0]

        # retrieve sub version number, ...
        cur_versnumber = cur_list[3]
        file_versnumber = file_list[3]

        # if cur number version is superior than file version, it's compatible
        if cur_versnumber >= file_versnumber:
            return 1

    # whatever the read error, we catch it
    except:
        pass

    return 0
