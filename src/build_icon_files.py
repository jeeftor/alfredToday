import sys, os
# Add local lib path to path
sys.path = [os.path.join(os.path.dirname(__file__), 'lib')] + sys.path

import lib.cairosvg as cairosvg

from workflow import Workflow3
from GoogleInterface import  GoogleInterface

def build_colors(self):
    colors = self.service.colors().get().execute()

    # Print available calendarListEntry colors.
    for id in colors['calendar']:
        color = colors['calendar'][id]
        print 'colorId: %s' % id
        print '  Background: %s' % color['background']
        print '  Foreground: %s' % color['foreground']
        # Print available event colors.
        for id, color in colors['event'].iteritem():
            print 'colorId: %s' % id
            print '  Background: %s' % color['background']
            print '  Foreground: %s' % color['foreground']



def main(wf):
    g = GoogleInterface(wf)


    colors = g.service.colors().get().execute()

    for id in colors['calendar']:


        color = colors['calendar'][id]
        bg_color = str(color['background'])


        out_fn = 'img/googleEvent_' + id + '.svg'

        with open('img/googleEvent.svg', 'r') as event_svg:
            data = event_svg.read().replace('#ABCDEF', bg_color)

            fo = open(out_fn, 'w')
            fo.write(data)
            fo.close()

            print "rsvg-convert -h 192 " + out_fn.replace('img/','') + " > " + out_fn.replace('img/','').replace('svg','png')

            # bytes = str.encode(data)
            # cairosvg.svg2png(bytestring=bytes, write_to='/tmp/out.png')

        # cairosvg.svg2png(
        #     url="/path/to/input.svg", write_to="/tmp/output.png")
        #
        # cairosvg.svg2pdf(
        #     file_obj=open("/path/to/input.svg", "rb"), write_to="/tmp/output.pdf")
        #
        # output = cairosvg.svg2ps(
        #     bytestring=open("/path/to/input.svg").read().encode('utf-8'))
        #
        # print 'colorId: %s' % id
        # print '  Background: %s' % color['background']
        # print '  Foreground: %s' % color['foreground']


if __name__ == '__main__':
    wf = Workflow3(libraries=['./lib'])
    log = wf.logger
    sys.exit(wf.run(main))

