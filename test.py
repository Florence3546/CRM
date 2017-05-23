#!/usr/bin/env python
import os
import sys

# import MySQLdb
import init_environ
import settings


import smtplib
from email.mime.text import MIMEText


MAIL_TO_LIST = ['zhengjiankang@paithink.com']
# MAIL_TO_LIST = ['zhengjiankang@paithink.com', 'shihuacheng@paithink.com', 'hh@paithink.com']
CONFIG_SMTP_PAITHINK = {'ip':'smtp.exmail.qq.com',
                        'port':25,
                        'user_id':'pskj@paithink.com',
                        'password':'ps123456',
                        'sender':'testcase<pskj@paithink.com>',
                        }

def send_email(sub, content):
    config = CONFIG_SMTP_PAITHINK

    msg = MIMEText(content, _subtype = 'html', _charset = 'utf-8')
    msg['Subject'] = sub
    msg['From'] = config.get('sender')
    msg['to'] = ';'.join(MAIL_TO_LIST)

    try:
        smtp = smtplib.SMTP()
        smtp.connect(config.get('ip'), config.get('port'))
        smtp.login(config.get('user_id'), config.get('password'))
        smtp.sendmail(config.get('sender'), MAIL_TO_LIST, msg.as_string())
    except Exception as e:
        print (e)

import django
from django.test.runner import DiscoverRunner

def collect_tests(test_suite, test_result):
    print 'collecting test result...'

    content = '<div>unittest run result:<div>'
    content += '<div>total: %s</div>' % (str(test_result.testsRun),)
    # content += '<table><tr><th>case</th><th>result</th></tr>'
    for item in test_suite:
        # content += '<tr><td>%s</td><td>%s</td></tr>' % (str(item), '')
        content += '<div>%s</div>' % (str(item),)
    # content += '</table>'

    content += '<br><div>failures:%d</div>' % (len(test_result.failures),)
    for t, msg in test_result.failures:
        content += '<div style="color:#ff0000">%s</div><div>%s</div>' % (str(t), str(msg))

    content += '<br><div>errors:%d<div>' % (len(test_result.errors),)
    for t, msg in test_result.errors:
        content += '<div style="color:#ff0000">%s</div><div>%s</div>' % (str(t), str(msg))

    return content

class unit_test_runner(DiscoverRunner):
    def run_tests(self, test_labels, extra_tests = None, **kwargs):
        print 'unit test runner running tests...'
        self.setup_test_environment()
        test_suite = self.build_suite(test_labels, extra_tests)
        old_config = self.setup_databases()
        test_result = self.run_suite(test_suite)
        self.teardown_databases(old_config)
        self.teardown_test_environment()
        return {'suite':test_suite, 'result':test_result}


class integration_test_runner(DiscoverRunner):
    def run_tests(self, test_labels, extra_tests = None, **kwargs):
        print 'integration test runner running tests...'
        self.setup_test_environment()
        test_suite = self.build_suite(test_labels, extra_tests)
        # old_config = self.setup_databases()
        test_result = self.run_suite(test_suite)
        # self.teardown_databases(old_config)
        self.teardown_test_environment()
        return {'suite':test_suite, 'result':test_result}


unit_test_conf = ('test.strategy_t.test_alg',)

if __name__ == "__main__":
    os.environ.update({"DJANGO_SETTINGS_MODULE": "settings"})
    django.setup()

    # print sys.argv
    execute_args = sys.argv[1:]
    # print execute_args

    if '-u' in execute_args:
        test_runner = unit_test_runner()
        results = test_runner.run_tests(test_labels = unit_test_conf)
        # content = collect_tests(test_suite = results.get('suite'), test_result = results.get('result'))
        # send_email('unit test result', content)
    elif '-i' in execute_args:
        test_runner = integration_test_runner()
        results = test_runner.run_tests(test_labels = unit_test_conf)
        # content = collect_tests(test_suite = results.get('suite'), test_result = results.get('result'))
        # send_email('unit test result', content)

    sys.exit(0)

