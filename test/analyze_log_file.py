# coding=UTF-8
'''分析错误日志'''
import init_environ
import glob

pathname = 'logs/*.log'
output_file = 'logs/result.txt'


def main():
    error_list = []
    filename_list = glob.glob(pathname)
    for filename in filename_list:
        with open(filename) as f:
            for line in f:
                if ', e=' in line and 'TopError' not in line and 'max number of clients reached' not in line:
                    error_list.append(line)
    with open(output_file, 'w') as f:
        f.writelines(error_list)

if __name__ == "__main__":
    main()
    print 'finish!'
