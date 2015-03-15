This is the web page for the gnb2wp script.

This script

Create a folder
Export your google notebooks to Atom format files in that folder
Export the intended WordPress blog to an XML file in that folder (WHY? gnb2wpb.py will use it to determine conversion parameters such as valid post ID range, GMT time offset, valid post to use as template for converting notebook entries, etc.)
Install HTML Tidy command line util for your platform
Install Python 2.4 or later (but not 3.0)
From a command shell, cd to your folder, run the script to generate a config (.INI) file like
gnb2wp.py -i iniFile.ini -w wordpress.2009-01-01.xml gnbFile1.xml gnbFile2.xml ...
Edit the generated .INI (in notepad, for instance) to suit your preferences
Rerun the script to generate import file with your settings like
gnb2wp.py -i iniFile -o wordpress\_import.xml
Upload wordpress\_import.xml into your wordpress blog
Verify that your blog has increased # posts same as stated when script ends
View each post that has your marker tag to verify it is ok and edit as necessary
Notes:
**your WP blog must have at least one post** guid and meta\_values do not seem to get overridden on import but
are filled in by WordPress if empty (guid) or absent (metaposts)
**post\_id of new posts use largest id + 1 and must ALL be unique in import file** not clear what meta keys do but they need to be large numbers
**import works only if output XML is tidied up, not sure why; so requires HTML Tidy** post\_name only keeps letters, digits and converts consecutive spaces
to one dash
**pubDate is not used for post date; rather post\_date and post\_date\_gmt** post\_date\_gmt must be inferred since GNB file only contains local time
**new tags will be automatically created by importer even if no wp:tag entries** script does a tad more than necessary because had to reverse-engineer what
is required vs optional... some of this was made difficult until discovered that
most posts would not import unless output was tidied up via HTML tidy...
Todo:
