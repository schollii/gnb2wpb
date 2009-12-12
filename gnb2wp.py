#!/usr/bin/env python
'''
All rights reserved. THIS COMMENT SECTION MAY NOT BE REMOVED OR MODIFIED 
IN ANY WAY without written permission by the author. 

Copyright (c) 2009 by Oliver Schoenborn <oliver.schoenborn@gmail.com>

Licensing:
* FOR HOME USE ONLY ie only for private use (NOT for businesses or 
  for revenue generation of any kind): This software may be used and 
  distributed according to the terms of the GNU General Public License 
  version 3, incorporated herein by reference.
* For Businesses and Commercial use: A separate commercial license 
  is available by contacting the author. 

USE OF THIS SCRIPT IS ENTIRELY AT YOUR OWN RISK. THE AUTHOR CAN NOT 
TAKE any responsibility for any negative impact on, or destruction of, your
blog. The author can however take full credit for any positive impact and 
donations are welcome. 

This script facilitates importing Google Notebook (GNB) entries into 
a WordPress (WP) blog. See https://code.google.com/p/gnb2wpb/wiki/MainPage
for usage and other information. 

'''

__VERSION__  = "1.0 (20091212)"
__AUTHOR__   = "Oliver L. Schoenborn"
__HOMEPAGE__ = "http://wp.me/PBTab-8i"

import os
import sys
import time
from datetime import datetime, timedelta

from ConfigParser import RawConfigParser

from xml.dom import minidom, Node
from xml.sax.saxutils import unescape


class Settings:
    testing = False
    iniFile = 'config.ini'
    wpTemplate = 'wordpress-export.xml'
    wpOutName = 'wordpress-import.xml'
    notebooks = []
    createIniFile = True
    overwriteIni = False
    templateStatus = 'publish'
    wpFirstPostID = 1
    offsetGMT = 0
    wpMarkerTagName = 'imported_from_gnb'
    

class ConfigFile(RawConfigParser):
    def __init__(self):
        self.__config = None

    def getWPLargestPostID(self, parent):
        postIDs = parent.getElementsByTagName('wp:post_id')
        largestPostID = 0
        for postID in postIDs:
            idVal = int( XMLUtils().getElemText(postID) ) 
            if idVal > largestPostID: 
                largestPostID = idVal
        Settings.wpFirstPostID = 1 + largestPostID
        assert Settings.wpFirstPostID > 0
        self.__config.set('Defaults', 'wpFirstPostID', Settings.wpFirstPostID)

    def getGMTOffset(self, parent):
        '''File all post_date and post_date_gmt elements in parent and 
        get a histogram of time diffs between each corresponding pair. 
        Set Settings.offsetGMT to the entry with highest frequency 
        in hours. So -5 indicates 5 hours east of GMT. '''
        deltaFreqs = {}
        mostFreqDelta = 0
        mostFreqDeltaFreq = 0
        timeFormat = '%Y-%m-%d %H:%M:%S'
        getText = XMLUtils().getText
        postDateGMTs = parent.getElementsByTagName('wp:post_date')
        for postDateGMT in postDateGMTs:
            postDate = getText(postDateGMT.parentNode, 'wp:post_date_gmt')
            try:
                pd = time.strptime(postDate, timeFormat)
                pdgmtStr = XMLUtils().getElemText(postDateGMT)
                pdgmt = time.strptime(pdgmtStr, timeFormat)
            except ValueError:
                continue # skip this entry, time data probably wrong
                
            # compute delta between post_date and post_date_gmt and track
            # which one is most common
            delta = (  datetime( *(pd[0:6]) ) 
                     - datetime( *(pdgmt[0:6])    ) )
            delta = delta.seconds/3600
            deltaFreqs.setdefault( delta, 0 )
            deltaFreqs[delta] += 1
            if deltaFreqs[delta] > mostFreqDeltaFreq:
                mostFreqDelta = delta
                mostFreqDeltaFreq = deltaFreqs[delta]
                
        print 'GMT delta found', mostFreqDelta
        Settings.offsetGMT = -mostFreqDelta
        self.__config.set('Defaults', 'offsetGMT', Settings.offsetGMT)
        
    def genIniFile(self):
        if not Settings.overwriteIni and os.path.exists(Settings.iniFile):
            print 'ERROR: file "%s" already exists, use -f to force overwrite' % Settings.iniFile
            sys.exit(3)
            
        self.__config = RawConfigParser()
        
        # Defaults section
        self.__config.add_section('Defaults')
        dom = minidom.parse(Settings.wpTemplate)
        categories = [catName.firstChild.data for catName in dom.getElementsByTagName('wp:cat_name')]
        self.__config.set('Defaults', 'wpAvailableCategories', ' | '.join(categories))
        self.__config.set('Defaults', 'wpDefaultCategory', categories[0])
        self.__config.set('Defaults', 'wpTemplate', Settings.wpTemplate)
        self.__config.set('Defaults', 'wpMarkerTagName', Settings.wpMarkerTagName)
        self.__config.set('Defaults', 'wpTemplateStatus', Settings.templateStatus)
        channels = dom.getElementsByTagName('channel')
        self.getWPLargestPostID(channels[0])
        self.getGMTOffset(channels[0])
        
        # One section per notebook
        for nb in Settings.notebooks:
            nbName = os.path.splitext(nb)[0]
            self.__config.add_section(nbName)
            self.__config.set(nbName, 'filename', nb)
            self.__config.set(nbName, 'category', 'One of your blog categories')
            #config.set(nbName, 'tag', 'One or more of your blog tags')
            
        iniOut = file(Settings.iniFile, 'w')
        self.__config.write(iniOut)
        iniOut.close()
        
    def __getParser(self):
        DEFAULT_CATEG = 'Imported from GNB'
        defaults = dict(
            defaultCategory = DEFAULT_CATEG, 
            availableCategories = DEFAULT_CATEG, 
            offsetGMT = '-5', 
            wpFirstPostID = '1',)
        self.__config = RawConfigParser(defaults)
        self.__config.read(Settings.iniFile)
        
    def getSettings(self):
        self.__getParser()

        # some parameters:
        Settings.wpTemplate = self.__config.get('Defaults', 'wpTemplate')
        Settings.wpFirstPostID = self.__config.getint('Defaults', 'wpFirstPostID')
        Settings.wpMarkerTagName = self.__config.get('Defaults', 'wpMarkerTagName')
        Settings.templateStatus = self.__config.get('Defaults', 'wpTemplateStatus')
        Settings.offsetGMT = self.__config.getfloat('Defaults', 'offsetGMT')
        DEFAULT_CATEG = self.__config.get('Defaults', 'wpDefaultCategory')
        Settings.DEFAULT_CATEG = DEFAULT_CATEG

        # available categories
        availCategs = self.__config.get('Defaults', 'wpAvailableCategories').split('|')
        availCategs = [categ.strip() for categ in availCategs]

        # done with Defaults section
        self.__config.remove_section('Defaults')
        
        # some sanity checks
        if DEFAULT_CATEG not in availCategs:
            print 'In defaults section: wpDefaultCategory must be one of the categories in wpAvailableCategories'
            sys.exit(7)
            
        # find all categories defined in wpTemplate and get nice name for each
        dom = minidom.parse(Settings.wpTemplate)
        categories = dom.getElementsByTagName('wp:category')
        niceCategNames = {}
        for categ in categories:
            catName = categ.getElementsByTagName('wp:cat_name')[0].firstChild.data
            catNiceName = XMLUtils().getText( categ, 'wp:category_nicename' )
            niceCategNames[catName] = catNiceName
            
        # remove the categories that are not in availCategs
        for categ in niceCategNames.keys():
            if categ not in availCategs:
                del niceCategNames[categ]
        assert set(niceCategNames) == set(availCategs)
        
        # finally we have our nice category names mapping and notebook names
        # and the only config sections left are one for each notebook
        Settings.niceCategNames = niceCategNames
        Settings.notebooks = self.__config.sections()[:] # copy
        
        return dom
        
    def getItems(self, notebook):
        return self.__config.items(notebook)


def printUsage():
    msg = '''
    Once you have exported your Google notebooks AND your WordPress 
    blog (into which you will be importing your Google notebook entries), 
    you can do 
    
        gnb2wp.py [-i iniFile] [-w wordpressFile] <list of notebooks>
    
    where 
    
    -i iniFile: override the default name used for the .INI file that will be 
        produced (defaults to %(defaultINI)s)
    -w wordpressFile: override the default name used for the .XML file of the 
        WordPress blog you exported (defaults to %(defaultWP)s)
    <list of notebooks>: (required) space-separated list of the notebook 
        files to convert. 
        
    For instance
    
        gnb2wp.py -w wordpress.2009-08-16.xml Household.xml "Software Development.xml"
    
    Once this is done and you have edited the .INI file to your liking, you do
    
        gnb2wp.py [-i iniFile] -o outputFile
        
    where
    
    -i iniFile: name of .INI file to use for settings; only needed if it was 
        overridden in first step
    -o outputFile: name of output file to produce

    For instance

        gnb2wp.py -o wordpress-export.xml
        
    See %(webpage)s for more details
    '''
    print msg % dict(
        defaultINI = Settings.iniFile, 
        defaultWP  = Settings.wpTemplate, 
        webpage    = __HOMEPAGE__)
    
    
def initFromCmdLine():
    ignoreNextArg = False
    for (indx, arg) in enumerate(sys.argv[1:]):
        argValIndx = indx+2
        
        if arg == '-v':
            print 'This is %s version %s by %s' % (sys.argv[0], __VERSION__, __AUTHOR__)
            
        elif arg == '-h':
            printUsage()
            sys.exit()
            
        elif arg == '-i':
            Settings.iniFile = sys.argv[argValIndx]
            ignoreNextArg = True
            
        elif arg == '-w':
            Settings.wpTemplate = sys.argv[argValIndx]
            ignoreNextArg = True
            
        elif arg == '-o':
            Settings.wpOutName = sys.argv[argValIndx]
            Settings.createIniFile = False
            ignoreNextArg = True
            
        elif arg == '-f':
            Settings.overwriteIni = True
            
        else:
            if ignoreNextArg:
                ignoreNextArg = False
            else:
                Settings.notebooks.append(arg)
    
    # show results:
    
    if Settings.createIniFile:
        print 'Will create INI:', `Settings.iniFile`
        print 'Will overwrite if exists:', Settings.overwriteIni
        print 'Will use WP template:', `Settings.wpTemplate`
        if Settings.notebooks:
            nbStr = ', '.join(`nb` for nb in Settings.notebooks)
            print 'Will use notebooks:', nbStr
        else:
            print 'ERROR: must specify at least one notebook file'
            sys.exit(1)
        
    else:
        print 'Will read INI:', `Settings.iniFile`
        print 'Will output WordPress import file to:', `Settings.wpOutName`
        if Settings.notebooks:
            nbStr = ', '.join(`nb` for nb in Settings.notebooks)
            print 'ERROR: must not specify notebook filenames with -w or -o:', nbStr
            sys.exit(2)
        

class XMLUtils:

    def clearAllChildren(self, element):
        for child in element.childNodes:
            element.removeChild(child)
            child.unlink()
    
    def setElemText(self, element, text, dom):
        self.clearAllChildren(element)
        textNode = dom.createTextNode(text)
        assert textNode.data == text
        element.appendChild(textNode)
    
    def replaceChildText(self, element, childTag, newTextStr, dom):
        # assume child of element has only one text node
        children = element.getElementsByTagName(childTag)
        for child in children:
            if child.childNodes: # then replace first:
                oldTextNode = child.childNodes[0]
                newTextNode = dom.createTextNode(newTextStr)
                child.replaceChild(newTextNode, oldTextNode)

    def removeAllChildrenByTagName(self, parentElem, childTag):
        children = parentElem.getElementsByTagName(childTag)
        for child in children:
            parentElem.removeChild(child)
            child.unlink()

    def clearCData(self, element, dom):
        for child in element.childNodes:
            element.removeChild(child)
            child.unlink()
        emptyCDATA = dom.createCDATASection('')
        element.appendChild(emptyCDATA)
            
    def getElemText(self, nodeElem):
        rc = ""
        for node in nodeElem.childNodes:
            if node.nodeType == node.TEXT_NODE:
                rc = rc + node.data
        return rc
        
    def getText(self, parent, elemName, indx=0): 
        elements = parent.getElementsByTagName(elemName)
        if len(elements) > indx:
            return self.getElemText( elements[0] )
        return None
        
    def insertBefore(self, elem, xml, **xmlMap):
        xml = '<root>%s</root>' % xml
        tempDom = minidom.parseString(xml % xmlMap)
        rootElem = tempDom.documentElement
        parent = elem.parentNode
        for child in rootElem.childNodes:
            assert child.parentNode is not parent
            parent.insertBefore(child, elem)
            assert child.parentNode is parent


class GNBConverter:
    class GNBEntry:
        def getTitleStr(self): pass
        def getDateStr(self, gmt=False): pass
        def getContentStr(self): pass
    
    def __init__(self, filename):
        self.__dom = minidom.parse(filename)
        
    def getDOM(self):
        return self.__dom
        
    def getEntries(self):
        '''Must return a list of objects derived from GNBEntry'''
        return []

        
class WPFromAtom(GNBConverter):
    def __init__(self, filename):
        GNBConverter.__init__(self, filename)
        
    def getEntries(self):
        entries = []
        items = self.getDOM().getElementsByTagName('entry')
        for item in items:
            content = item.getElementsByTagName('content')
            if content and content[0].hasAttributes():
                gnbEntry = self.WPItemFromAtom( content[0].parentNode )
                entries.append(gnbEntry)
                
        return entries                        
    
    class WPItemFromAtom(GNBConverter.GNBEntry):
        def __init__(self, atomEntry):
            self.__atomEntry = atomEntry
                
        def getTitleStr(self):
            titleStr = XMLUtils().getText( self.__atomEntry, 'title' )
            
            return titleStr
            
        def getDateStr(self, gmt=False):
            rawDateStr = XMLUtils().getText( self.__atomEntry, 'updated' )
            ts = time.strptime(rawDateStr.split('.',1)[0], '%Y-%m-%dT%H:%M:%S')
            dt = datetime( * (ts[0:6]) )
            # dt.strftime('%a, %d %b %Y %H:%M:%S +0000') # 'Wed, 26 Sep 2007 21:56:46 +0000'
            if gmt:
                dt += timedelta(hours = - Settings.offsetGMT)
            return dt.strftime('%Y-%m-%d %H:%M:%S')

        def getContentStr(self):
            content = self.__atomEntry.getElementsByTagName('content')
            assert content[0].getAttribute('type') == 'html'
            content = unescape( XMLUtils().getElemText(content[0]) )
            links = self.__atomEntry.getElementsByTagName('link')
            if links:
                link = links[0].getAttribute('href')
                linkTitle = links[0].getAttribute('title')
                content += '<p>\nLink: <a href="%s">%s</a>\n' % (link, linkTitle)
            return content

            
def getPostNameFromTitle(titleStr):
    postName = []
    for char in titleStr:
        if char.isspace(): char = '-' # convert spaces to '-'
        if char.isalpha() or char.isdigit() or char == '-':
            if char != '-' or (postName is None) or postName[-1] != char: 
                postName.append(char.lower())
    postName = ''.join(postName)
    return postName


assert getPostNameFromTitle('AbC + 123 == -1') == 'abc-123-1'


def createWPItem(itemTemplate, dom, postID, category, niceCategName, gnbEntry):
    newWPItem = itemTemplate.cloneNode(True)

    # title, post name, link:
    titleStr = gnbEntry.getTitleStr()
    #print 'New WP Item for GBN entry "%s"' % titleStr
    XMLUtils().replaceChildText(newWPItem, 'title', titleStr, dom)
    postName = getPostNameFromTitle(titleStr)
    XMLUtils().replaceChildText(newWPItem, 'wp:post_name', postName, dom)
    # looks like post_name and link could be anything, will be replaced by WP importer
    XMLUtils().replaceChildText(newWPItem, 'link', 'http://a.com/'+postName, dom)
    
    # post ID
    postIDElems = newWPItem.getElementsByTagName('wp:post_id')
    assert len(postIDElems) == 1
    XMLUtils().setElemText(postIDElems[0], str(postID), dom)
    # if guid emptied, will be generated by WordPress importer
    XMLUtils().replaceChildText(newWPItem, 'guid', '', dom)
    
    # category
    guidElem = newWPItem.getElementsByTagName('guid')
    xml = '''<category>
                <![CDATA[%(categ)s]]>
                </category>
             <category domain="category" nicename="%(nice)s">
                <![CDATA[%(categ)s]]>
                </category>
          '''
    XMLUtils().insertBefore(guidElem[0], xml, nice = niceCategName, categ = category)
    
    # tag
    if Settings.wpMarkerTagName:
        xml = '''<category domain="tag">
                  <![CDATA[%(marker)s]]>
                  </category>
                <category domain="tag" nicename="%(marker)s">
                  <![CDATA[%(marker)s]]>
                  </category>
            '''
        XMLUtils().insertBefore(guidElem[0], xml, marker = Settings.wpMarkerTagName)
    
    # date: format (GMT) 'Wed, 26 Sep 2007 21:56:46 +0000'
    newDateStr = gnbEntry.getDateStr()
    XMLUtils().replaceChildText(newWPItem, 'pubDate', newDateStr, dom) # will be overridden
    XMLUtils().replaceChildText(newWPItem, 'wp:post_date', newDateStr, dom)
    newDateGMTStr = gnbEntry.getDateStr(gmt=True)
    XMLUtils().replaceChildText(newWPItem, 'wp:post_date_gmt', newDateGMTStr, dom)
    
    # content
    content = gnbEntry.getContentStr()
    cdata = newWPItem.getElementsByTagName('content:encoded')[0].firstChild
    cdata.data = content

    # post-meta: want large values, all different; HACK: base it on postID
    metaValues = newWPItem.getElementsByTagName('wp:meta_value')
    offset = 0
    for metaValNode in metaValues:
        offset += 1
        arbitraryFF = 12345 # fudge factor
        XMLUtils().setElemText(metaValNode, str((postID+offset)*arbitraryFF), dom)
        
    return newWPItem

    
def getGNBConverter(filename):
    if not filename.endswith('.xml'):
        print '   Only XML files supported currently, skipping'
        return None

    return WPFromAtom(filename)
    
    
def createWPItems(parentElem, itemTemplate, config):
    postID = Settings.wpFirstPostID
    for notebook in Settings.notebooks:
        print 'Loading notebook "%s"' % notebook

        options = dict( config.getItems(notebook) )
        filename = options['filename']
        
        wpCategory = options.get('category', Settings.DEFAULT_CATEG)
        niceCategName = Settings.niceCategNames[wpCategory]
            
        print '   Will read from "%s", use categ "%s"' % (filename, wpCategory)
        
        gnb2wp = getGNBConverter(filename)
        if gnb2wp:
            gnbDOM = gnb2wp.getDOM()
            for gnbEntry in gnb2wp.getEntries():
                wpItem = createWPItem(itemTemplate, gnbDOM, postID, wpCategory, 
                    niceCategName, gnbEntry)
                parentElem.appendChild( wpItem )
                postID += 1
                
                # only do less than 15 posts so easy to remove from WP:
                if Settings.testing and postID >= 13 + Settings.wpFirstPostID:
                    return 
        

def createTemplateItem(itemElements, dom):
    itemElement = None
    for element in itemElements:
        status = XMLUtils().getText(element, 'wp:status')
        postType = XMLUtils().getText(element, 'wp:post_type')
        if (status == Settings.templateStatus) and (postType == 'post'):
            itemElement = element
            break
    if itemElement is None:
        print 'ERROR: could not find an <item> that had %s as status' % Settings.templateStatus
        sys.exit(6)
        
    # Create the template that will be used for each notebook entry
    itemTemplate = itemElement.cloneNode(True)
    
    # remove all comments, categories, tags and other content we don't want
    XMLUtils().removeAllChildrenByTagName(itemTemplate, 'category')
    XMLUtils().removeAllChildrenByTagName(itemTemplate, 'wp:comment')
    XMLUtils().removeAllChildrenByTagName(itemTemplate, 'wp:postmeta')
    
    # clear the content nodes
    XMLUtils().replaceChildText(itemTemplate, 'description', '', dom)
    contentNodes = itemTemplate.getElementsByTagName('content:encoded')
    assert len(contentNodes) == 1
    XMLUtils().clearCData(contentNodes[0], dom)
    excerptNodes = itemTemplate.getElementsByTagName('excerpt:encoded')
    assert len(excerptNodes) == 1
    XMLUtils().clearCData(excerptNodes[0], dom)
    
    return itemTemplate

    
def cleanupParentElem(parentElem):
    XMLUtils().removeAllChildrenByTagName(parentElem, 'item')


def outputWPImportFile(dom):
    out = dom.toxml(encoding="UTF-8")
    outObj = file(Settings.wpOutName, 'w')
    outObj.write(out)
    outObj.close()
    postsCreated = len(dom.getElementsByTagName('content:encoded'))
    print 'Created %s new posts in "%s"' % (postsCreated, Settings.wpOutName)
    
    cmd = 'tidy -q -xml -m "%s"' % Settings.wpOutName
    print 'Tidying up the output file via %s' % `cmd`
    os.system(cmd)
    
    # HTML Tidy will have put \n around every CDATA which seems 
    # to confuse WP so remove them
    dom = minidom.parse(Settings.wpOutName)
    contentItems = dom.getElementsByTagName('content:encoded')
    for content in contentItems:
        for child in content.childNodes:
            if child.nodeType != child.CDATA_SECTION_NODE:
                #print 'removing spurious node', child
                content.removeChild(child)
                child.unlink()

    # save again
    out = dom.toxml(encoding="UTF-8")
    outObj = file(Settings.wpOutName, 'w')
    outObj.write(out)
    outObj.close()
    

def genWPImportFile():
    config = ConfigFile()
    dom = config.getSettings()
    items = dom.getElementsByTagName('item')
    if len(items) < 1:
        print 'ERROR: need at least one post in template file!'
        sys.exit(4)
        
    parentElem = items[0].parentNode
    itemTemplate = createTemplateItem(items, dom)
    cleanupParentElem(parentElem)    
    createWPItems(parentElem, itemTemplate, config)
    
    outputWPImportFile(dom)
    
    print 'You can now import "%s" into your blog' % Settings.wpOutName
    
    
initFromCmdLine()

if Settings.createIniFile:
    config = ConfigFile()
    config.genIniFile()
    
else:
    genWPImportFile()
    
    