from workflow import Workflow3


def main(wf):
    '''This function will do MAGIC UPDATE MAGIC for outlook'''

    # Check to see if updates are available
    if wf.update_available:
            wf.start_update()

if __name__ == '__main__':
    wf = Workflow3(libraries=['./lib'],
                   update_settings={
                       'github_slug': 'jeeftor/alfredToday',
                       'frequency': 7}
                   )
    wf.run(main)