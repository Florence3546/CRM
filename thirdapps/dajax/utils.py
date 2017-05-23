"""
Some util terminal colors.
"""

def print_red(text):
	print "\033[40m\033[1;31m%s\033[0m" % text

def print_green(text):
	print "\033[40m\033[1;32m%s\033[0m" % text
	
def print_green_start():
	print "\033[40m\033[1;32m"

def print_red_start():
	print "\033[40m\033[1;31m"
		
def print_blue_start():
	print "\033[40m\033[1;36m"

def print_clear():
	print "\033[0m"