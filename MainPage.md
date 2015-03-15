# Introduction #

This is the usage page for the gnb2wp script.

**WARNING: USE THE SCRIPT AT YOUR OWN RISK! I haven't had any problems, but due to the nature of the export-import process, it is impossible to test for all faulty or even fatal configuration, so YMMV!**


# Details #

This script is designed to be used in two stages:

  1. generate configuration (.INI) file: the script uses information from your WordPress blog, and from your Google notebooks, to create a default configuration. You may then edit this configuration to suit your preferences.
  1. generate import file: the script uses the configuration to extract all notebook entries from your notebook files and put them in the specfied import file.

Here are the details:

  1. Create a temporary folder on your computer
  1. Export your google notebooks to Atom (.XML) format files in that folder.
    * You can do this via "Manage Notebooks" or by clicking on Tools for each notebook. See snapshot A at GoogleExports.
    * Unfortunately there doesn't seem to be a way of exporting all notebooks at once but it shouldn't be too bad for 90% of notebookers, who will only have 5-6 notebooks.
    * Best format is Atom. This is only available via the "Manage Notebooks" link in the Notebooks panel.
    * For some reason, for one of my notebooks the Atom export failed with HTTP 404 error (not found). So I may add support for notebooks exported in HTML format too. See snapshot B at GoogleExports.
  1. Export the intended WordPress blog to an XML file in that folder. WHY? Because this is currently the only way for the script to get the required info from your blog. Only a small part of the blog export is used, but it is crucial nonetheless. Example data is valid post ID range, GMT time offset, a post to use as template for converting notebook entries, etc. **NOTE** that your WP blog must have at least one post.
  1. From a command shell, cd to your folder, run the script to generate a config (.INI) file like
```
gnb2wp.py -w wordpress.2009-01-01.xml gnbFile1.xml gnbFile2.xml ...
```
  1. Edit the generated .INI (in notepad or jot, for instance) to suit your preferences
  1. Rerun the script to generate the WordPress import file like
```
gnb2wp.py -o wordpress_import.xml
```
  1. Upload `wordpress_import.xml` into your wordpress blog. See the notes below.


**Additional suggestions:**

  * This script has so far only been tested on my Google notebooks and my WordPress blog around Dec 2009. Please let me know of your successes/failures so that everyone can benefit! You can post on the [group](http://groups.google.com/g/gnb2wpb|support). Include date, script version, tidy version, python version, WordPress version.
  * For your own peace of mind, you should probably create a temporary blog (easily done if your blog is on WordPress.com, probably also easy for self-hosted), and import there first, just to see that the HTML imported from your Google Notebook entries hasn't screwed anything up. You can then either directly import into the real blog, or (probably better) export from the temporary blog into the real blog.
  * Verify that your blog has increased its number of posts by same number as output in the command shell when script ends. For instance the script will output `Created 95 new posts in ...` if 95 notebook entries were found.
  * Each entry will have a tag as per your config file. View each post that has that tag to verify it is ok and edit as necessary