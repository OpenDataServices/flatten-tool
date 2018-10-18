def isint(string):
    try:
        int(string)
        return True
    except ValueError:
        return False

def parse_sheet_configuration(configuration_list):
    configuration = {}
    for item in configuration_list:
        parts = item.split()
        if (len(parts) == 2 and parts[0].lower() == "skiprows" and isint(parts[1])):
            configuration['skipRows'] = max(int(parts[1]), 0)
        if (len(parts) == 2 and parts[0].lower() == "headerrows" and isint(parts[1])):
            configuration['headerRows'] = max(int(parts[1]), 1)
        if (len(parts) == 1 and parts[0].lower() == "ignore"):
            configuration['ignore'] = True
        if (len(parts) == 1 and parts[0].lower() in ("hashcomments", "hashcomment")):
            configuration['hashcomments'] = True
        if (len(parts) == 2 and parts[0].lower() == "xmlroottag"):
            configuration['XMLRootTag'] = parts[1]
        if (len(parts) == 2 and parts[0].lower() == "rootlistpath"):
            configuration['RootListPath'] = parts[1]
        if (len(parts) == 2 and parts[0].lower() == "idname"):
            configuration['IDName'] = parts[1]
    return configuration
