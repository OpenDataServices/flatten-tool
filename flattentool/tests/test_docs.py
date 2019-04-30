import os
import shlex
import subprocess
import sys
import uuid

from os.path import join, getsize
from six import text_type


def test_examples_in_docs():

    with open('examples/receipt/source-map/expected.json', 'rb') as fp:
        expected = fp.read()
        for expected_filename in [
            'normalised/expected.json',
            'combine-table-into-cafe/expected.json',
            'combine-table-into-cafe-2/expected.json',
        ]:
            with open('examples/receipt/'+expected_filename, 'rb') as fp2:
                assert fp2.read() == expected, "Files differ: examples/receipt/source-map/expected.json, examples/receipt/{}".format(expected_filename)
    tests_passed = 0
    for root, dirs, files in os.walk('examples'):
        for filename in files:
            if 'xlsx' in root and sys.version_info[:2] < (3,4):
                continue
            if 'cmd.txt' in filename:
                if os.path.exists(join(root, 'actual')) and os.path.isdir(join(root, 'actual')):
                    os.rename(join(root, 'actual'), join(root, 'actual.'+text_type(uuid.uuid4())))
                os.mkdir(join(root, 'actual'))
                expected_return_code = 0
                expected_stdout = b''
                if os.path.exists(join(root, 'expected_return_code.txt')):
                    with open(join(root, 'expected_return_code.txt'), 'rb') as fp:
                        expected_return_code = int(fp.read().strip())
                with open(join(root, filename), 'rb') as fp:
                    cmds = text_type(fp.read(), 'utf8').strip().split('\n')
                    actual_stdout = b''
                    actual_stderr = b''
                    for cmd in cmds:
                        assert (
                            cmd.startswith('$ flatten-tool ') or cmd.startswith('$ cat ')
                        ), "Expected commands to start with '$ flatten-tool'. This doesn't: {}".format(cmd)
                        # Since we are defining all the commands ourselves, this is reasonably safe
                        cmd_parts = shlex.split(cmd[len('$ '):])
                        # Include coverage output in the results
                        if cmd_parts[0] == 'flatten-tool':
                            cmd_parts = [
                                'coverage',
                                'run',
                                '--source', 'flattentool',
                                '--parallel-mode',
                            ] + cmd_parts
                        process = subprocess.Popen(cmd_parts, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        (cmd_actual_stdout, cmd_actual_stderr) = process.communicate()
                        process.wait()
                        assert process.returncode == expected_return_code, cmd
                        actual_stdout += (cmd_actual_stdout or b'')
                        actual_stderr += (cmd_actual_stderr or b'')
                if os.path.exists(join(root, 'expected')) and os.path.isdir(join(root, 'expected')):
                    # Create case
                    assert len(os.listdir(join(root, 'expected'))) == len(os.listdir(join(root, 'actual'))), "Different number of files. {}".format(cmds)
                    for expected_filename in os.listdir(join(root, 'expected')):
                        assert os.path.exists(join(root, 'actual', expected_filename)), "File {} was not generated {}".format(expected_filename, cmds)
                        with open(join(root, 'expected', expected_filename), 'rb') as fp_expected:
                            with open(join(root, 'actual', expected_filename), 'rb') as fp_actual:
                                assert _strip(fp_actual.read()) == _strip(fp_expected.read()), "File {} has unexpected content. {}".format(expected_filename, cmds)
                    expected_stdout = b''
                # Flatten case
                if os.path.exists(join(root, 'expected.txt')):
                    with open(join(root, 'expected.txt'), 'rb') as fstdout:
                        expected_stdout = fstdout.read()
                elif os.path.exists(join(root, 'expected.json')):
                    with open(join(root, 'expected.json'), 'rb') as fstdout:
                        expected_stdout = fstdout.read()
                elif os.path.exists(join(root, 'expected.xml')):
                    with open(join(root, 'expected.xml'), 'rb') as fstdout:
                        expected_stdout = fstdout.read()
                if 'help' in root:
                    # Ignore whitespace differences for help messages
                    assert b' '.join(actual_stdout.split()) == b' '.join(expected_stdout.split())
                else:
                    assert _strip(actual_stdout) == _strip(expected_stdout), "Different stdout: {}".format(cmds)
                expected_stderr = b''
                if os.path.exists(join(root, 'expected_stderr_partial.txt')):
                    with open(join(root, 'expected_stderr_partial.txt'), 'rb') as fstderr:
                        data = fstderr.read()
                    assert data in actual_stderr
                if os.path.exists(join(root, 'expected_stderr.json')):
                    with open(join(root, 'expected_stderr.json'), 'rb') as fstderr:
                        data = fstderr.read()
                        expected_stderr_lines = text_type(data, 'utf8').split('\n')
                        for line in expected_stderr_lines:
                            if line:
                                expected_stderr += (line + '\n').encode('utf8')
                            else:
                                 expected_stderr += b'\n'
                    assert _simplify_warnings(_strip(actual_stderr)) == _simplify_warnings(_strip(expected_stderr)), "Different stderr: {}".format(cmds)
                tests_passed += 1
    # Check that the number of tests were run that we expected
    if sys.version_info[:2] < (3,4):
        assert tests_passed == 51
    else:
        assert tests_passed == 52

def _simplify_warnings(lines):
    return '\n'.join([_simplify_line(line) for line in lines.split('\n')])

def _simplify_line(line):
    if 'DataErrorWarning: ' in line:
        return line[line.find('DataErrorWarning: '):]
    return line

# Older versions of Python have an extra whitespace at the end compared to newer ones
# https://bugs.python.org/issue16333
def _strip(output):
    # Don't worry about any extra blank lines at the end either
    outstr = text_type(output, 'utf8').rstrip('\n')
    return '\n'.join(line.rstrip(' ') for line in outstr.split('\n'))


# Useful for a coverage check - see developer docs for how to run the check
if __name__ == '__main__':
    test_examples_in_docs()
