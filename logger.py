"""
This file is used only to test widgets separately from the main program.
It is not used in the main program. It alows for ex: use external signals which are
handled by the main program... ignore config file etc.

"""
from inspect import currentframe, getframeinfo
from datetime import datetime
class LOGGER:
    def __init__(self,level:str = "ALL"):
        self.treshold_level = level
        self.levels_to_numbers = {
            "CRITICAL":0,
            "ERROR":1,
            "WARNING":2,
            "HARDWARE":3,
            "SIGNAL":4,
            "DEBUG":5,
            "INFO":6,
            "UNNECESSARY" :7,
            "ALL":8,
        }
        
 

    def log(self, message:str = "", level:str = "ALL", oneline = True):
        if self.levels_to_numbers[level] <= self.levels_to_numbers[self.treshold_level]:
            line_number = getframeinfo(currentframe().f_back).lineno
            file = getframeinfo(currentframe().f_back).filename
            line_string = f'"{file}", line {line_number}'

            if oneline:
                message = message.replace("\r","\\r").replace("\n","\\n")


            prefix_to_show = message.split(":")[0]#delete this
            prefix_to_show = f"\033[34m{prefix_to_show}\033[0m"
            message = ":".join(message.split(":")[1:])#delete this
            level, message = self.colorLevels(level,message)
            line_string = f"\033[36m{line_string}\033[0m" #style it yellow
            #print(f'{level:<14} :: {message:<80} :: {datetime.now()} :: {line_string}')
            print(f'{prefix_to_show}: {message:<80}')
        
    def colorLevels(self,level,message):
        if level == "CRITICAL":
            level_new = f"\033[31m{level}\033[0m" #red
            message_new =  f"\033[31m{message}\033[0m" #red

        elif level == "ERROR":
            level_new = f"\033[31m{level}\033[0m" #red
            message_new =  f"\033[31m{message}\033[0m" #red

        elif level == "WARNING":
            level_new = f"\033[33m{level}\033[0m" #yellow
            message_new =  f"\033[33m{message}\033[0m" #yellow
        
        elif level == "DEBUG":
            level_new = f"\033[35m{level}\033[0m" #purple
            message_new =  f"\033[32m{message}\033[0m" #purple

        elif level == "HARDWARE":
            level_new = f"\033[35m{level}\033[0m" #purple
            message_new =  f"\033[35m{message}\033[0m" #purple

        elif level == "INFO":
            level_new = f"\033[34m{level}\033[0m" #blue
            message_new =  f"\033[32m{message}\033[0m" #blue
        elif level == "UNNECESSARY":
            level_new = f"\033[34m{level}\033[0m" #blue
            message_new =  f"\033[32m{message}\033[0m" #blue
        elif level == "ALL":
            level_new = f"\033[34m{level}\033[0m" #blue
            message_new =  f"\033[32m{message}\033[0m" #blue

        elif level == "SIGNAL":
            level_new = f"\033[33m{level}\033[0m" #blue
            message_new =  f"\033[32m{message}\033[0m" #blue
        
        return level_new, message_new