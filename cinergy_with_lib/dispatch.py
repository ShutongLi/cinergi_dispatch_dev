import pandas as pd
import numpy as np
from lxml import etree
from Distribution import DistObj
import regex as re
import requests

# pre-condition: documentID, user, full_notebook_url

NSMAP = {"gmi":"http://www.isotc211.org/2005/gmi",
    "gco":"http://www.isotc211.org/2005/gco",
    "gmd":"http://www.isotc211.org/2005/gmd",
    "gml":"http://www.opengis.net/gml",
    "gmx":"http://www.isotc211.org/2005/gmx",
    "gts":"http://www.isotc211.org/2005/gts",
    "srv":"http://www.isotc211.org/2005/srv",
    "xlink":"http://www.w3.org/1999/xlink"}

#the table for organizational tokens
tbl1 = pd.read_csv('resources/tbl1.csv')
tbl1['TestCode'] = tbl1['TestCode'].fillna('def f(): return {}')
#compile the functions stored in the table
for code in tbl1['TestCode']:
    exec(code)

#do the same for table for basic file extensions tokens
tbl1_base = pd.read_csv('resources/tbl1_2.csv')
tbl1['TestCode'] = tbl1['TestCode'].fillna('def f(): return {}')
for code in tbl1_base['TestCode']:
    exec(code)

#tbl2 is for mapping tokens to the links to corresponding platforms
tbl2 = 'https://docs.google.com/spreadsheet/ccc?key=1jFGjp2_QRT1z2YR4DJZwA-OTaj41zpdkUiX_JxBoISU&gid=123788411&output=csv'
tbl2 = pd.read_csv(tbl2).replace(np.nan, '')
# tbl2 = tbl2.loc[tbl2['token'] != '']
# tbl2['Label'] = [str(i) for i in range(tbl2.shape[0])]


def testurl(theurl):
    # try HEAD first in case the response document is big
    # print('trying ' + theurl)
    try:
        r = requests.head(theurl)
        if r.status_code != requests.codes.ok:
            # check GET in case is an incomplete http implementation
            r = requests.get(theurl)
            if r.status_code == requests.codes.ok:
                return True
            else:
                return False
        else:
            return True
    except:
        return False


def whole_process(documentID, type = 'org'):
    if type == 'org':
        metadataURLx = construct_md_url(documentID)
        tree = get_etree(metadataURLx)
        distlist = get_distributions(tree)
        token_dist = dists_to_token(distlist, table=tbl1)
        label_actionable = token_to_actionable_menu(tbl2, token_dist)
        return label_actionable
    elif type == 'base':
        metadataURLx = construct_md_url(documentID)
        tree = get_etree(metadataURLx)
        distlist = get_distributions(tree)
        token_dist = dists_to_token(distlist, table=tbl1_base)
        label_actionable = token_to_actionable_menu(tbl2, token_dist)
        return label_actionable
    else:
        print('indicated process type unknown')
        return {}


def construct_md_url(documentID):
    catalogURL = "http://datadiscoverystudio.org/geoportal/"
    metadataURLx = catalogURL + 'rest/metadata/item/' + documentID + '/xml'
    return metadataURLx


def get_etree(metadataURLx):
    tree = etree.parse(metadataURLx)
    return tree


def get_distributions(tree):
    distlist = []
    for elt in tree.getiterator("{http://www.isotc211.org/2005/gmd}MD_DigitalTransferOptions"):
        # only want OnlineResources that are in distribution//MD_DigitalTransferOptions
        #  TBD-- figure out what to do with CI_OnlineResource inside SV_OperationMetadata

        # iterate through CI_OnlineResource elements
        for onlineres in elt.getiterator("{http://www.isotc211.org/2005/gmd}CI_OnlineResource"):

            if ((onlineres.find("gmd:linkage/gmd:URL", namespaces=NSMAP) is not None) and
                    (onlineres.find("gmd:linkage/gmd:URL", namespaces=NSMAP).text is not None)):
                theURL = onlineres.find("gmd:linkage/gmd:URL", namespaces=NSMAP).text
            else:
                theURL = 'empty'

            # print('theURL ' + theURL + '\n')

            if (onlineres.find("gmd:name/gco:CharacterString", namespaces=NSMAP) is not None):
                thename = onlineres.find("gmd:name/gco:CharacterString", namespaces=NSMAP).text
            else:
                thename = ''

            if (onlineres.find("gmd:description/gco:CharacterString", namespaces=NSMAP) is not None):
                thedescription = onlineres.find("gmd:description/gco:CharacterString", namespaces=NSMAP).text
            else:
                thedescription = ''

            if (onlineres.find("gmd:protocol/gco:CharacterString", namespaces=NSMAP) is not None):
                theprotocol = onlineres.find("gmd:protocol/gco:CharacterString", namespaces=NSMAP).text
            else:
                theprotocol = ''

            if (onlineres.find("gmd:applicationProfile/gco:CharacterString", namespaces=NSMAP) is not None):
                theappprofile = onlineres.find("gmd:applicationProfile/gco:CharacterString", namespaces=NSMAP).text
            else:
                theappprofile = ''

            if (onlineres.find("gmd:function/gmd:CI_OnLineFunctionCode", namespaces=NSMAP) is not None):
                thefunctioncode = onlineres.find("gmd:function/gmd:CI_OnLineFunctionCode", namespaces=NSMAP).get(
                    "codeListValue")
            else:
                thefunctioncode = ''

            if (onlineres.find("gmd:function/gmd:CI_OnLineFunctionCode", namespaces=NSMAP) is not None):
                thefunctiontext = onlineres.find("gmd:function/gmd:CI_OnLineFunctionCode", namespaces=NSMAP).text
            else:
                thefunctiontext = ''

            # print('\n Distribution: name-%s;\n  url- %s; \n  description--%s; \n   protocol-%s, app profile- %s; function- %s; %s' %
            #      (thename,theURL,thedescription,theprotocol,theappprofile,thefunctioncode,thefunctiontext))

            # Handle format and distributor organization
            # have to figure out who is the distributor
            # check to see if have multiple distributors, if so they should have distributor formats and transfer options
            #   if they don't then assume all formats apply to all distributions
            formatlist = []  # initialize

            if len(onlineres.xpath("./ancestor::gmd:MD_Distribution/gmd:distributor", namespaces=NSMAP)) <= 1:
                # have zero or one distributor;
                distorg = ''
                if len(onlineres.xpath("./ancestor::gmd:MD_Distribution/gmd:distributor", namespaces=NSMAP)) == 1:
                    dist = onlineres.xpath("./ancestor::gmd:MD_Distribution/gmd:distributor", namespaces=NSMAP)[0]
                    if len(dist.xpath("gmd:MD_Distributor//gmd:organisationName", namespaces=NSMAP)) > 0:
                        distorg = \
                        dist.xpath("gmd:MD_Distributor//gmd:organisationName/child::node()/text()", namespaces=NSMAP)[0]
                # print("distorg: " + distorg)
                # get formats. Formats might be on Distribution, Distributor, or DigitalTransferOption
                thedistformats = onlineres.xpath("./ancestor::gmd:MD_Distribution/gmd:distributionFormat",
                                                 namespaces=NSMAP)
                # get formats at gmd:MD_Distribution/gmd:distributionFormat/gmd:MD_Format
                for aformat in thedistformats:
                    if ((aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString", namespaces=NSMAP) is not None) and
                            (aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString",
                                          namespaces=NSMAP).text not in formatlist)):
                        formatlist.append(
                            aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString", namespaces=NSMAP).text)

                thedistformats = onlineres.xpath("./ancestor::gmd:MD_DigitalTransferOptions/gmd:distributionFormat",
                                                 namespaces=NSMAP)
                # get formats on the parent gmd:MD_DigitalTransferOptions
                for aformat in thedistformats:
                    if ((aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString", namespaces=NSMAP) is not None) and
                            (aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString",
                                          namespaces=NSMAP).text not in formatlist)):
                        formatlist.append(
                            aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString", namespaces=NSMAP).text)

                thedistformats = onlineres.xpath("./ancestor::gmd:MD_Distribution//gmd:distributorFormat",
                                                 namespaces=NSMAP)
                # get formats on the gmd:MD_Distributor; the transfer options might not be child of distributor
                for aformat in thedistformats:
                    if ((aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString", namespaces=NSMAP) is not None) and
                            (aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString",
                                          namespaces=NSMAP).text in formatlist)):
                        formatlist.append(
                            aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString", namespaces=NSMAP).text)

            elif len(onlineres.xpath("./ancestor::gmd:MD_Distributor", namespaces=NSMAP)) == 1:
                # MD_DigitalTransferOptions is child of MD_Distributor; there are multiple distributors
                distorg = ''
                dist = onlineres.xpath("./ancestor::gmd:MD_Distributor", namespaces=NSMAP)[0]
                if len(dist.xpath("gmd:distributorContact//gmd:organisationName", namespaces=NSMAP)) > 0:
                    distorg = \
                    dist.xpath("gmd:distributorContact//gmd:organisationName/child::node()/text()", namespaces=NSMAP)[0]
                # print("distorg: " + distorg)

                # check if they have distributorFormat
                thedistformats = onlineres.xpath("./ancestor::gmd:MD_Distributor/gmd:distributorFormat",
                                                 namespaces=NSMAP)
                # get formats on the gmd:MD_Distributor; note in this case look for specific distributor that is parent
                #   of the digital transfer options/online resource.
                for aformat in thedistformats:
                    if ((aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString", namespaces=NSMAP) is not None) and
                            (aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString",
                                          namespaces=NSMAP).text in formatlist)):
                        formatlist.append(
                            aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString", namespaces=NSMAP).text)

                thedistformats = onlineres.xpath("./ancestor::gmd:MD_DigitalTransferOptions/gmd:distributionFormat",
                                                 namespaces=NSMAP)
                # get formats specific to the parent gmd:MD_DigitalTransferOptions
                for aformat in thedistformats:
                    if ((aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString", namespaces=NSMAP) is not None) and
                            (aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString",
                                          namespaces=NSMAP).text not in formatlist)):
                        formatlist.append(
                            aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString", namespaces=NSMAP).text)

                thedistformats = onlineres.xpath("./ancestor::gmd:MD_Distribution/gmd:distributionFormat",
                                                 namespaces=NSMAP)
                # get formats at gmd:MD_Distribution/gmd:distributionFormat; assume these apply to all digital transfer options
                for aformat in thedistformats:
                    if ((aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString", namespaces=NSMAP) is not None) and
                            (aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString",
                                          namespaces=NSMAP).text not in formatlist)):
                        formatlist.append(
                            aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString", namespaces=NSMAP).text)

            else:
                # multiple distributors, but digital transfer options are not associated with specific distributor

                distorg = ''
                # arbitrarily take the first distributor organization
                dist = onlineres.xpath("./ancestor::gmd:MD_Distribution/gmd:distributor", namespaces=NSMAP)[0]
                if len(dist.xpath("gmd:MD_Distributor//gmd:organisationName", namespaces=NSMAP)) > 0:
                    distorg = \
                    dist.xpath("gmd:MD_Distributor//gmd:organisationName/child::node()/text()", namespaces=NSMAP)[0]
                # print("distorg: " + distorg)

                #  assume all distributors offer all digital transfer options and formats that are child of distribution
                thedistformats = onlineres.xpath("./ancestor::gmd:MD_DigitalTransferOptions/gmd:distributionFormat",
                                                 namespaces=NSMAP)
                # get formats specific to the parent gmd:MD_DigitalTransferOptions
                for aformat in thedistformats:
                    if ((aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString", namespaces=NSMAP) is not None) and
                            (aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString",
                                          namespaces=NSMAP).text not in formatlist)):
                        formatlist.append(
                            aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString", namespaces=NSMAP).text)

                thedistformats = onlineres.xpath("./ancestor::gmd:MD_Distribution/gmd:distributionFormat",
                                                 namespaces=NSMAP)
                # get formats at gmd:MD_Distribution/gmd:distributionFormat; assume these apply to all digital transfer options
                for aformat in thedistformats:
                    if ((aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString", namespaces=NSMAP) is not None) and
                            (aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString",
                                          namespaces=NSMAP).text not in formatlist)):
                        formatlist.append(
                            aformat.find("gmd:MD_Format/gmd:name/gco:CharacterString", namespaces=NSMAP).text)

            thisdistobj = DistObj(thename)
            # thisdistobj.name = thename
            # print("theName: " + thename)
            thisdistobj.url = theURL
            thisdistobj.description = thedescription
            thisdistobj.protocol = theprotocol
            thisdistobj.appprofile = theappprofile
            thisdistobj.functioncode = thefunctioncode
            thisdistobj.functiontext = thefunctiontext
            thisdistobj.distorg = distorg
            thisdistobj.formatlist = formatlist

            distlist.append(thisdistobj)

    return distlist


def dists_to_token(distlist, table = tbl1):
    result_list = []
    f_list = list(table['expression'].dropna())
    for dist in distlist:
        for f in f_list:
            function_locals = locals()
            # print(function_locals)
            result_list += [eval(f)]
    token_dist = combine_dcts(result_list)

    return token_dist


def combine_dcts(dct_list):
    # combining a list of dicts into a single dict, duplicated keys will have their values in a list
    combined = {}
    for dct in dct_list:
        # print(dct)
        for key in dct.keys():
            if key in combined.keys():
                combined[key] += [dct[key]]
            else:
                combined[key] = [dct[key]]
    return combined


def token_to_actionable_menu(token_url_sheet, token_dist):
    # return a dictionary with keys of application label and values of application's actionable url
    # the dict will be

    # ah shit, it's gonna be ugly
    label_actionable = {}
    for token in token_dist.keys():
        # actionables is the sub-table of the token_url_sheet that only has rows regarding the specific token
        actionables = token_url_sheet.loc[token_url_sheet['token'] == token]
        dist_list = token_dist[token]

        # TO-DO
        for i in range(actionables.shape[0]):
            row = actionables.iloc[i, :]
            app_name = row['Label']
            url_template = row['Web application URL']
            for dist in dist_list:
                dist_name = dist['name'][:50]
                dist_url = dist['url']
                menu_label = dist_name + "-" + app_name
                url = token_url_template(url_template, dist_url)
                label_actionable[menu_label] = url
    return label_actionable


def token_url_template(url_template, dist_url):
    final_url = re.sub('{.*}', dist_url, url_template)
    return final_url







