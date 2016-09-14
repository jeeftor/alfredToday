import sys
import argparse
from workflow import Workflow, ICON_WEB, ICON_WARNING, ICON_NOTE, web, PasswordNotFound, Workflow3

def main(wf):
    def googleFilter(filename):
        return 'google' in filename

    def exchangeFilter(filename):
        return 'exchange' in filename

    import os
    from workflow.notify import notify

    key =  os.environ['settings_value']
    value =  os.environ['value_to_store']


    wf.logger.debug("        Key: %s", key)
    wf.logger.debug("      Value: %s", value)

    if key == 'password':
        wf.save_password('today.workflow.password',value)
        notify('Password updated')
    else:
        wf.settings[key] = {'value':value}

        # wf.store_data(key, value)
        text = os.environ['text_to_display']

        if key == 'use_google':
            wf.clear_cache(googleFilter)

            if value == '0':
                notify("Google Calendar Support", u'\u274C Disabled')
            else:
                notify("Google Calendar Support", u'\u2705 Enabled')

        elif key == 'use_exchange':
            wf.clear_cache(exchangeFilter)
            if '0' == value:
                notify("Exchange Server Support", u'\u274c Disabled')
            else:
                notify("Exchange Server Support", u'\u2705 Enabled')
        elif key == 'use_ntlm':

            def exchangeFilter(filename):
                return 'exchange' in filename

            # Clear outlook events because we are changing the auth type
            wf.clear_cache(exchangeFilter)

           # outlook_events = wf.cached_data(outlook_cache_key, outlook_wrapper, max_age=cache_time)

            if '0' == value:
                notify("NTLM Authentication", u'\u274c Disabled')
            else:
                notify("NTLM Authentication", u'\u2705 Enabled')
        else:
            notify('Updated ' + text, "To: " + value)


if __name__ == u"__main__":
    wf = Workflow3(libraries=['./lib'])
    wf.logger.debug('      _______________  ____  ______  ')
    wf.logger.debug('     / ___/_  __/ __ \/ __ \/ ____/  ')
    wf.logger.debug('     \__ \ / / / / / / /_/ / __/  ')
    wf.logger.debug('    ___/ // / / /_/ / _, _/ /___  ')
    wf.logger.debug('   /____//_/  \____/_/ |_/_____/  DATA  ')
    wf.logger.debug('     ')
    sys.exit(wf.run(main))