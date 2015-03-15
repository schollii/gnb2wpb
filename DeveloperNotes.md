# Notes #

  * guid and meta\_values do not seem to get overridden on import but
are filled in by WordPress if empty (guid) or absent (metaposts)
  * post\_id of new posts use largest id + 1 and must ALL be unique in import file
  * not clear what meta keys do but they need to be large numbers
  * import works only if output XML is tidied up, not sure why; so requires HTML Tidy
  * post\_name only keeps letters, digits and converts consecutive spaces
to one dash
  * pubDate is not used for post date; rather post\_date and post\_date\_gmt
  * post\_date\_gmt must be inferred since GNB file only contains local time
  * new tags will be automatically created by importer even if no wp:tag entries
  * script does a tad more than necessary because had to reverse-engineer what
is required vs optional... some of this was made difficult until discovered that
most posts would not import unless output was tidied up via HTML tidy...

# Todo #

