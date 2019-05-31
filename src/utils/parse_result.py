"""
Parsing mortar testing results from results.json under each test result

    "TestSleepySanityNeedle": {
        "suite_id": 17561,
        "test01_ValidNode": {
            "test": true,
            "tearDown": true,
            "setUp": true,
            "case_id": 22740483
        },
        "test02_Pairing": {
            "test": true,
            "tearDown": true,
            "setUp": true,
            "case_id": 22740484
        },
         ....
    }
"""

import json
import os
import argparse
import subprocess
import re


def result_parser(result_folder, summary_filename='summary_log'):

    summary_fp = open(summary_filename, 'w+')

    result_all_dict = {}

    for _, tc_result_folder_list, _ in os.walk(result_folder):
        for tc_result_folder in tc_result_folder_list:
            tc_result_path = os.path.join(result_folder, tc_result_folder)
            for _, _, file_list in os.walk(tc_result_path):
                for file in file_list:
                    if file != 'results.json':
                        continue

                    result = {}

                    if 'src.log' in file_list and not 'TestFwUpgrade' in tc_result_folder:
                        mortar_log_path = os.path.join(result_folder, tc_result_folder, 'src.log')
                        ncp_version, wpantund_version, linux_host_version, rtos_shell_version, cast_fm_version = get_sw_version(mortar_log_path)
                        result['ncp_version'] = ncp_version
                        result['wpantund_version'] = wpantund_version
                        result['linux_host_version'] = linux_host_version
                        result['rtos_shell_version'] = rtos_shell_version
                        result['cast_fm_version'] = cast_fm_version
                    else:
                        result['ncp_version'] = 'Unknown'
                        result['wpantund_version'] = 'Unknown'
                        result['linux_host_version'] = 'Unknown'
                        result['rtos_shell_version'] = 'Unknown'
                        result['cast_fm_version'] = 'Unknown'

                    filename = os.path.join(result_folder, tc_result_folder, file)

                    f = open(filename)

                    data = json.load(f)

                    #print data

                    print

                    summary_fp.write('\r\n')

                    testcase_suit = data.keys()[0]
                    result_all_dict[testcase_suit] = {}
                    result_all_dict[testcase_suit]['testcase'] = {}
                    result_all_dict[testcase_suit]['log_path'] = tc_result_path
                    suite_result = 'PASS'

                    for testcase in data.values():
                        for testcase_name, test_result in sorted(testcase.items()):
                            temp = []

                            if testcase_name == 'suite_id':
                                continue

                            if test_result['test']:
                                result[testcase_name] = 'PASS'
                                result_all_dict[testcase_suit]['testcase'][testcase_name] = 'PASS'
                            else:
                                suite_result = 'FAIL'

                                if not test_result['setUp']:
                                    temp.append('setUp failed')

                                if 'pings_sent' in test_result and 'pings_received' in test_result:
                                    if test_result['pings_sent'] != test_result['pings_received']:
                                        temp.append('F: {} out of {}'.format(test_result['pings_sent']-test_result['pings_received'], test_result['pings_sent']))
                                else:
                                    if 'Ping' in testcase_name:
                                        temp.append('No Pings')
                                    else:
                                        temp.append('FAIL')
                                if not test_result['tearDown']:
                                    temp.append('tearDown failed')
                                result[testcase_name] = temp

                                result_all_dict[testcase_suit]['testcase'][testcase_name] = ' '.join(temp)

                    result_all_dict[testcase_suit]['result'] = suite_result


                    print 'Test results for {}:'.format(testcase_suit)
                    summary_fp.write('Test results for {}: {}'.format(testcase_suit, suite_result))
                    summary_fp.write('\r\n')

                    if not testcase_suit.startswith('TestFwUpgrade'):

                        if result['cast_fm_version'] != 'Unknown':

                            str1 = 'Cast Firmware Version: {}'.format(result['cast_fm_version'])
                            print str1
                            summary_fp.write(str1+'\r\n')

                        if result['linux_host_version'] != 'Unknown':
                            if 'FlintstonePinna' in testcase_suit:
                                str1 = 'Flintstone Firmware Version: {}'.format(result['linux_host_version'])
                            else:
                                str1 = 'Agate HU Firmware Version: {}'.format(result['linux_host_version'])
                            print str1
                            summary_fp.write(str1+'\r\n')

                        if result['rtos_shell_version'] != 'Unknown':
                            if 'FlintstonePinna' in testcase_suit:
                                str1 = 'Pinna Firmware Version: {}-Diagonostics'.format(result['rtos_shell_version'])
                            else:
                                str1 = 'Agate HL Firmware Version: {}-Diagonostics'.format(result['rtos_shell_version'])
                            print str1
                            summary_fp.write(str1+'\r\n')

                        str1 = 'Marble Software version: {}'.format(result['ncp_version'])
                        print str1
                        summary_fp.write(str1+'\r\n')

                        str2 = 'Wpantund Software version: {}'.format(result['wpantund_version'])
                        print str2
                        summary_fp.write(str2 + '\r\n')

                    for k, v in sorted(result.items()):
                        if 'version' not in k:
                            str1 = k + ' '*(40-len(k)) + ''.join(v)
                            print str1

                            summary_fp.write(str1+'\r\n')

    return result_all_dict


def get_sw_version(mortar_logfile):
    """
    Get software version from mortar.log:

    example for NCP and wpantund:
    grep - e "NCP is running" - e "Driver is running" mortar.log
    [2018-06-04 06:18:35,113] [mortar.Needle-7e60.wpantund] [DEBUG] wpantund[124338]: NCP is running "OPENTHREAD/1.0d532; Marble-Needle1; Jun  1 2018 20:36:42"
    [2018-06-04 06:18:35,113] [mortar.Needle-7e60.wpantund] [DEBUG] wpantund[124338]: Driver is running "0.08.00d-nest (0.07.00-nest-697-g9fffe3f; May 31 2018 15:24:55)"

    AgateHL:
    shell-1.0d299-agate-diagnostics

    AgateHU:
    Linux version 4.1.15-5.9d266 (bamboo@bamboo-agent-155-v16-prod) (gcc version 5.2.0 (GCC) ) #1 PREEMPT Thu Jun 21 06:25:53 UTC 2018

    F1:
    [2018-06-25 15:42:45,172] [mortar.router] [DEBUG] [    0.000000] Linux version 4.1.15-1.2a25 (bamboo@bamboo-agent-010-v16-prod) (gcc version 5.2.0 (GCC) ) #1 PREEMPT Wed Jun 20 04:18:08 UTC 2018

    P1:
    [2018-06-25 15:42:31,222] [mortar.Pinna-ED] [DEBUG] shell-1.2a7-pinna-diagnostics

    """
    ncp_version, wpantund_version, linux_host_version, rtos_shell_version = 'Unknown', 'Unknown', 'Unknown', 'Unknown'
    cast_fm_version = 'Unknown'

    try:
        lines = subprocess.check_output(['grep', '-e', 'NCP is running', '-e', 'Driver is running', '-e', 'Linux version',
                                         '-e', 'shell-', '-e', 'Cast Firmware version',  mortar_logfile])
    except:
        print 'Grepping versions by subprocess returned -1 !!!!'

    else:
        for line in lines.split('\n'):

            if 'OPENTHREAD' in line:
                ncp_version = line[line.index('OPENTHREAD'):-2]
            elif 'Driver is running' in line:
                wpantund_version = line[line.index('running')+8:-2]
            elif 'Linux version' in line and not 'from Linux version' in line:
                linux_host_version = re.findall(r'Linux version [0-9a-z.]+-([0-9a-z.]+)', line)[0]
            elif 'shell-' in line:
                rtos_shell_version = line.split()[-1].split('-')[1]
            elif 'Cast Firmware version' in line:
                cast_fm_version = line.split(':')[-1]

    return ncp_version, wpantund_version, linux_host_version, rtos_shell_version, cast_fm_version


def parse_args():
    """Parse the arguments."""
    parser = argparse.ArgumentParser(description="Parsing Mortor test results")

    parser.add_argument('-f', '--file_path',help="Mortor test result log path")

    parser.add_argument('-o', '--output', help="Output file path, default: summary.log", default='summary.log')

    args = vars(parser.parse_args())

#    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    result_folder = args['file_path']
    summary_filename = args['output']

    result_parser(result_folder, summary_filename)


def test():

    result_folder = '/opt/nest/openthread_test/results/silk_run_0221/test_run_on_02-21-08:18/'

    rel = result_parser(result_folder)

    print
    for k, v in rel.items():
        print k
        for k1, v1 in v.items():
            print k1, v1
        print


if __name__ == '__main__':
    main()

    #test()