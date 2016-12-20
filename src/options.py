from workflow import Workflow3
import sys




def main(wf):
    pass


if __name__ == u"__main__":
    wf = Workflow3(libraries=['./lib'],update_settings={
        'github_slug': 'jeeftor/alfredToday',
        'frequency': 7
    })

    sys.exit(wf.run(main))