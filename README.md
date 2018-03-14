# CrossRef Metadata Source for Calibre

This is a metadata source plugin for Calibre which downloads metadata for
work from the [CrossRef](https://crossref.org) API.

This plugin is heavily derived from the CrossRef plugin by Panagiotis Vlantis:
https://github.com/maxchaos/calibre-crossref. The difference is that this
plugin does not rely on the Habanero CrossRef API library, as it only uses
a very small subset of the API, and it therefore also does not require the
Python Requests library either.

## Using the plugin

The plugin can be installed either by saving the ZIP file for a release, or
by building the ZIP from this source.

To build the zip file, but not install it:

    make zip

To build and install into Calibre:

    make install

Uninstall with:

    make uninstall

THe plugin is used like any other metadata source plugin. Make sure it's
enabled in the list of active metadata source plugins (the gear icon next
to the `Download Metadata` button in the Edit view.

Works that have a DOI in their ID list will be looked up using that, otherwise
the title and authors will be used. The following field are populated:

* Title
* Authors
* Publication date (as best known - there are several dates provided by CrossRef)
* Publisher (e.g. Elsevier)
* Series (used for the journal name)
* Series index ((ab)used for the Volume and Issue)

## Testing

There are a couple of tests in `test.py`. You can run these by building,
installing and then running like so:

    make test

## Changelog

*1.0.0*: Initial release.
