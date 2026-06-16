class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'



BLACK = bcolors.OKCYAN + u'\u25a0' + bcolors.ENDC
WHITE = bcolors.ENDC + u'\u25a1'
X_char = bcolors.WARNING + u'\u2612' + bcolors.ENDC