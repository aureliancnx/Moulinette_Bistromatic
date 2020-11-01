import json
import re
import subprocess
import sys
import time
from random import randrange
from time import sleep
import atexit

tests = 0
test_report = ''

def exit_handler():
    file = 'report.txt'
    with open(file, 'w') as filetowrite:
        filetowrite.write(test_report)
    print("\033[93m[MOULI] \x1b[0m{0} tests passés.".format(tests))

def bc_eq(test_name, expr, base, ops):
    start_time = time.time()
    bc = get_bc(expr, None)
    end_time = (time.time() - start_time)
    assert_eq(test_name, expr, base, ops, bc, 0, end_time)

def bc_customeq(test_name, expr, base, ops, bc_custom):
    start_time = time.time()
    bc = get_bc(expr, bc_custom)
    end_time = (time.time() - start_time)
    assert_eq(test_name, expr, base, ops, bc, 0, end_time)

def filter_nonprintable(text):
    import itertools
    nonprintable = itertools.chain(range(0x00,0x20),range(0x7f,0xa0))
    return text.translate({character:None for character in nonprintable})

def assert_eq(test_name, expr, base, ops, expected, exit_code, bc_time):
    global tests
    global test_report
    start_time = time.time()
    expected = filter_nonprintable(expected)
    test_report = test_report + "~> echo '{0}' | ./calc '{1}' '{2}' '{3}'\n".format(expr, base, ops, str(len(expr)))
    output = filter_nonprintable(get_output('./calc', expr, base, ops))
    end_time = (time.time() - start_time)
    result_excode = get_exitcode('./calc', expr, base, ops)

    if exit_code != result_excode:
        if result_excode < 0:
            test_report = test_report + "Test crashed: Exit code: {0}\n".format(result_excode)
            print("\033[93m[MOULI] \x1b[0;30;41m{0} : Test crashed:\x1b[0m".format('./calc'))
            print("\033[93m[MOULI] \x1b[0;30;41mEXPR: {0} | BASE: {1} | OPS: {2}\x1b[0m".format(expr, base, ops))
            exit(84)
        else:
            print("\033[93m[MOULI] \x1b[0;30;41m{0} : Exit code difference:\x1b[0m".format('./calc'))
            test_report = test_report + "Wrong exit code: {0} | Expected: {1}\n".format(result_excode, exit_code)
            print("\033[93m[MOULI] \x1b[0;30;41mEXPR: {0} | BASE: {1} | OPS: {2}\x1b[0m".format(expr, base, ops))
            print("\033[93m[MOULI] Expected exit code:\x1b[0m")
            print(exit_code)
            print("\033[93m[MOULI] But got exit code:\x1b[0m")
            print(result_excode)
            print("\033[93m[MOULI] Test failed: {0}\x1b[0m".format(test_name))
            exit(84)

    test_report = test_report + "{0}\n".format(output)
    if not expected.__eq__(output):
        test_report = test_report + "\nFAILURE. Expected: {0}\n".format(expected)
        print("\033[93m[MOULI] \x1b[0;30;41m{0} : Output difference:\x1b[0m".format('./calc'))
        print("\033[93m[MOULI] \x1b[0;30;41mEXPR: {0} | BASE: {1} | OPS: {2}\x1b[0m".format(expr, base, ops))
        print("\033[93m[MOULI] Expected:\x1b[0m")
        print("'{0}'".format(expected))
        print("\033[93m[MOULI] But got:\x1b[0m")
        print("'{0}'".format(output))
        print("\033[93m[MOULI] Test failed: {0}\x1b[0m".format(test_name))
        exit(84)
    tests += 1
    if bc_time == -1:
        print("\033[93m[MOULI] \x1b[0mTest {0} : PASSED. (Expr length: {1} | Exec time: {2}s)\x1b[0m".format(test_name, str(len(expr)), "{:.2f}".format(end_time)))
    else:
        print("\033[93m[MOULI] \x1b[0mTest {0} : PASSED. (Expr length: {1} | Exec time: {2}s | BC time: {3}s)\x1b[0m".format(test_name,
                                                                                                                             str(len(
                                                                                                                                 expr)),
                                                                                                                             "{:.2f}".format(
                                                                                                                                 end_time),
                                                                                                                             "{:.2f}".format(
                                                                                                                                 bc_time),
                                                                                                                             ))


# Get the output from an executable
def get_output(file, expr, base, ops):
    popen = subprocess.Popen((file, base, ops, str(len(expr))), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             stdin = subprocess.PIPE)
    popen.stdin.write(bytes(expr, 'utf-8'))
    popen.stdin.close()
    popen.wait(10)
    output = popen.stdout.read()
    return output.decode("utf-8").replace('\n', '').rstrip('\n')

# Get the exitcode from an executable
def get_exitcode(file, expr, base, ops):
    popen = subprocess.Popen((file, base, ops, str(len(expr))), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             stdin = subprocess.PIPE)
    popen.stdin.write(bytes(expr, 'utf-8'))
    popen.stdin.close()
    popen.wait(10)
    return popen.returncode

# Get the output from bc
def get_bc(expr, args):
    popen = subprocess.Popen(('bc'), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             stdin=subprocess.PIPE)
    if args is not None:
        popen.stdin.write(bytes(args + expr + '\n', 'utf-8'))
    else:
        popen.stdin.write(bytes(expr + '\n', 'utf-8'))
    popen.stdin.close()
    popen.wait(2)
    output = popen.stdout.read()
    return output.decode("utf-8").replace('\n', '').replace('\\', '').rstrip('\n')


# Run tests
def run_tests():
    tests = None

    try:
        file = open("tests.json", "r")
        content = file.read()
        tests = json.loads(content)
    except:
        print("\033[93m[MOULI] Unable to read tests.json file.")
        exit(84)

    for i in tests:
        if i['type'] == 'assert_eq':
            assert_eq(i['name'], i['expression'], i['base'], i['operators'], i['expected_output'], i['expected_exitcode'], -1)
        elif i['type'] == 'bc_eq':
            bc_eq(i['name'], i['expression'], i['base'], i['operators'])
        elif i['type'] == 'bc_customeq':
            bc_customeq(i['name'], i['expression'], i['base'], i['operators'], i['bc_custom'])


def main(argv):
    atexit.register(exit_handler)
    print("\033[93m[MOULI] \x1b[0;30;44mRunning tests...\x1b[0m")
    run_tests()
    print("\033[93m[MOULI] \x1b[6;30;42mEverything seems izoké.\x1b[0m")


if __name__ == "__main__":
    main(sys.argv[1:])