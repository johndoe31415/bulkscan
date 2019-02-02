# bulkscan
bulkscan is a document organizing software that runs locally and uses the
browser as a UI. It makes heavy use of ES6 on the client side and has a Python
server component that does all the processing in the background. Internally,
all scanned documents are converted into a self-designed "MUD" (Multi-Document)
file format. Essentially, it are sqlite3 database files which contain all the
data and metadata.

After long consideration, this is what I went with this solution because it
allows me to contain in a single (document) file many pages that have maybe
been resized and enhanced while retaining the originals. It also allows to
perform OCR once and store only the additional text data in there for later
rendering as a PDF.

WARNING: This software is not considered stable by any strech of the
imagination. Development is mainly driven by my need to get my documents in
order.

## Third-party code
bulkscan uses several projects internally, namely:

  * For autocompletion, the [Pixabay Autocompletion Code](https://github.com/Pixabay/JavaScript-autoComplete)
    is used, licensed under the MIT license.
  * For doing formatting from ES6, [Alexandru Mărășteanu's sprintf implementation](https://github.com/alexei/sprintf.js)
    is used, licensed under BSD-3.
  * For styling, [Pure.CSS is used](https://purecss.io/), licensed under the
    BSD/MIT License (see the original license file for details).

## Dependencies
bulkscan requires sane (for scanning), ImageMagick (for converting images),
Python3 (for all the web logic), uwsgi (as a webserver).

## License
All my code is licensed under the GNU GPL-3.
