from workflow import  Workflow3

def main(wf):

    ckeys = ['exchange.Today', 'exchange.Tomorrow', 'google.Today', 'google.Tomorrow']

    for key in ckeys:
        print (key + " " + str(wf.cached_data(key)))

if __name__ == '__main__':
    wf = Workflow3(libraries=['./lib'],
                   )
    log = wf.logger

    wf.run(main)
