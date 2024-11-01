def remountLine(line):
    content = ' '.join([_.text for _ in line.find_all('word')])
    return content