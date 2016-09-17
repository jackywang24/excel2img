# -*- coding: utf-8 -*-
#  Copyright 2016 Alexey Gaydyukov
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os
import sys

class ExcelFile(object):
    @classmethod
    def open(cls, filename):
        obj = cls()
        obj._open(filename)
        return obj

    def __init__(self):
        self.app = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        return False

    def _open(self, filename):
        excel_pathname = os.path.abspath(filename)  # excel requires abspath
        if not os.path.exists(excel_pathname):
            raise IOError('No such excel file: %s', filename)

        try:
            from pywintypes import com_error
            import win32com.client
            # Using DispatchEx to start new Excel instance, to not interfere with
            # one already possibly running on the desktop
            self.app = win32com.client.DispatchEx('Excel.Application')
        except:
            raise OSError('Failed to start Excel')

        try:
            self.workbook = self.app.Workbooks.Open(excel_pathname, ReadOnly=True)
        except:
            self.close()
            raise IOError('Failed to open %s'%filename)

    def close(self):
        self.workbook.Close(SaveChanges=False)


def export_img(fn_excel, fn_image, page=None, _range=None):
    """ Exports images from excel file """

    output_ext = os.path.splitext(fn_image)[1].upper()
    if output_ext not in ('.GIF', '.BMP', '.PNG'):
        parser.error('Unsupported image format: %s'%output_ext)

    # if both page and page-less range are specified, concatenate them into range
    if _range is not None and page is not None and '!' not in _range:
        _range = "%s!%s"%(page, _range)

    with ExcelFile.open(fn_excel) as excel:
        if _range is None:
            if page is None: page = 1
            try:
                rng = excel.workbook.Sheets(page).UsedRange
            except com_error:
                raise Exception("Failed locating used cell range on page %s"%page)
        else:
            try:
                rng = excel.workbook.Application.Range(_range)
            except com_error:
                raise Exception("Failed locating range %s"%(_range))
        xlScreen, xlPrinter = 1, 2
        xlPicture, xlBitmap = -4147, 2
        rng.CopyPicture(xlScreen, xlBitmap)
        from PIL import ImageGrab, PILLOW_VERSION
        # PIL >= 3.3.1 required to work well with Excel screenshots
        assert tuple(int(x) for x in PILLOW_VERSION.split('.')) >= (3,3,1), "PIL >= 3.3.1 required"
        im = ImageGrab.grabclipboard()
        im.save(fn_image, fn_image[-3:])


if __name__ == '__main__':

    from optparse import OptionParser
    parser = OptionParser(usage='''%prog excel_filename image_filename [options]\nExamples:
            %prog test.xlsx test.png
            %prog test.xlsx test.png -p Sheet2
            %prog test.xlsx test.png -r MyNamedRange
            %prog test.xlsx test.png -r 'Sheet3!B5:C8'
            %prog test.xlsx test.png -r 'Sheet4!SheetScopedNamedRange' ''')
    parser.add_option('-p', '--page', help='pick a page (sheet) by page name. When not specified (and RANGE either not specified or doesn\'t imply a page), first page will be selected')
    parser.add_option('-r', '--range', metavar='RANGE', dest='_range', help='pick a range, in Excel notation. When not specified all used cells on a page will be selected')
    opts, args = parser.parse_args()

    if len(args) != 2:
        parser.print_help(sys.stderr)
        parser.exit()

    export_img(args[0], args[1], opts.page, opts._range)