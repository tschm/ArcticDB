import sys
import xml.etree.ElementTree as ET


def transform_testcase(suite_prefix, class_prefix, num, testcase):
    """
    Takes a <testcase> element, corrects some of its attributes, and returns it
    wrapped in a <testsuite> element to hack around some odd assumptions in the
    Jenkins JUnit plugin.
    """

    # Prepend class name for test splitting purposes.
    classname = testcase.get('classname')
    if classname:
        testcase.set('classname', '{}.{}'.format(class_prefix, classname))

    # Wrap each testcase tag in a testsuite tag with a unique name to work
    # around test duration math in the Jenkins JUnit plugin.
    suite = ET.Element('testsuite')
    suite.set('tests', '1')
    suite.set('name', '{}-{}'.format(suite_prefix, num))
    suite.append(testcase)
    return suite


def main():
    if len(sys.argv) != 5:
        print('Usage: {} <testsuite prefix> <class prefix> <input xml> <output xml>'.format(sys.argv[0]))
        sys.exit(1)

    _, suite_prefix, class_prefix, infile, outfile = sys.argv

    tree = ET.parse(infile)

    # Wrap each <testcase> element we can find in its own <testsuite> element,
    # put them all in a <testsuites> tag, and write the tree to outfile.
    suites = ET.Element('testsuites')
    suites.extend((
        transform_testcase(suite_prefix, class_prefix, i, testcase)
        for i, testcase in enumerate(tree.findall('.//testcase'))))
    ET.ElementTree(suites).write(outfile)


if __name__ == '__main__':
    main()
