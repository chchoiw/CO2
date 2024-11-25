import logging
from functools import wraps
class mylogger(logging.Logger):
    # https://github.com/python/cpython/blob/3.13/Lib/logging/__init__.py

    def __init__(self, name, logFolder, level=0, sio=None, name_space="echo"):
        # super(FooChild,self) 首先找到 FooChild 的父类（就是类 FooParent），然后把类 FooChild 的对象转换为类 FooParent 的对象
        super().__init__(name=name, level=level)    
        self.sio=sio
        self.name_space=name_space


        super().setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        # logFolder = config["logFolder"]
        # logDtStr = datetime.datetime.now().strftime("%Y%m%d")

        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)-8s - %(name)-12s - %(message)s')
        # file_handler = logging.FileHandler(
        #     logFolder+'_{}.txt'.format(logDtStr))
        self.file_handler = logging.handlers.TimedRotatingFileHandler(
            logFolder+"main", when='d', interval=1, backupCount=365, encoding='utf-8')
        self.file_handler.suffix = "%Y%m%d_%H%M.log"
        self.console_handler.setFormatter(formatter)
        self.file_handler.setFormatter(formatter)
        super().addHandler(self.console_handler)
        super().addHandler(self.file_handler)
    
    def getLogger(self,loggerName):
        super().getLogger(loggerName)
        # self.sio.emit('responseData', {'csvStr': csvStr}, namespace=self.name_space)
    def wrapEmit(func):
        """
        Decorator to wrap chainable commands, allowing for immediate execution
        of the wrapped command by passing in an `execute=True` kwarg.

        """
        @wraps(func)
        def addAndExec(self,msg, *args, **kwargs):

            func(self, msg,*args, **kwargs)
            self.sio.emit('log', {'data': msg}, namespace=self.name_space)
            print("wrapmsg",msg)
        return addAndExec

    @wrapEmit
    def info(self, msg, *args, **kwargs):
        
        if len(args) == 1 and isinstance(args[0], str):
            msg1=args.pop()
            msgNew = " {:<15}: {}".format( msg,msg1)
        else:
            msgNew=msg
        super().info(msgNew, *args, **kwargs)
        # print("print str",str)

    @wrapEmit
    def warning(self, msg, *args, **kwargs):
        """
        Delegate a warning call to the underlying logger.
        """
        if len(args) == 1 and isinstance(args[0], str):
            msg1=args.pop()
            msgNew = " {:<15}: {}".format( msg,msg1)
        else:
            msgNew=msg
        super().warning(msgNew, *args, **kwargs)

    @wrapEmit
    def error(self, msg, *args, **kwargs):
        """
        Delegate an error call to the underlying logger.
        """
        if len(args) == 1 and isinstance(args[0], str):
            msg1=args.pop()
            msgNew = " {:<15}: {}".format( msg,msg1)
        else:
            msgNew=msg
        super().error(msgNew, *args, **kwargs)

    @wrapEmit
    def exception(self, msg, *args, exc_info=True, **kwargs):
        """
        Delegate an exception call to the underlying logger.
        """
        if len(args) == 1 and isinstance(args[0], str):
            msg1=args.pop()
            msgNew = " {:<15}: {}".format( msg,msg1)
        else:
            msgNew=msg
        super().exception(msgNew, *args, **kwargs)

        #super(mylogger,self).info(str)
    @wrapEmit
    def critical(self, msg, *args, **kwargs):
        """
        Delegate a critical call to the underlying logger.
        """
        if len(args) == 1 and isinstance(args[0], str):
            msg1=args.pop()
            msgNew = " {:<15}: {}".format( msg,msg1)
        else:
            msgNew=msg
        super().critical(msgNew, *args, **kwargs)



# config = {
#     "logFolder": "picarro_log/",
#     "logStart": "True",
#     "dataFolder": "picarro_data/"
# }
# # logger2 = logging.getLogger('mylogger')

# logger=mylogger("mylogger")
# logger.setLevel(logging.DEBUG)
# console_handler = logging.StreamHandler()
# if config["logStart"] in ["True", "true", "TRUE"]:
#     logFolder = config["logFolder"]
#     #logDtStr = datetime.datetime.now().strftime("%Y%m%d")
#     logDtStr="test"
#     file_handler = logging.FileHandler(
#         logFolder+'_{}.txt'.format(logDtStr))
#     formatter = logging.Formatter(
#         '%(asctime)s - %(levelname)s - %(message)s')
#     console_handler.setFormatter(formatter)
#     file_handler.setFormatter(formatter)
#     logger.addHandler(console_handler)
#     logger.addHandler(file_handler)
# logger.info("test")
