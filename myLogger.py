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
        file_handler = logging.handlers.TimedRotatingFileHandler(
            logFolder+"main", when='d', interval=1, backupCount=365, encoding='utf-8')
        file_handler.suffix = "%Y%m%d_%H%M.log"
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        super().addHandler(console_handler)
        super().addHandler(file_handler)
    
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
        super().info(msg, *args, **kwargs)
        # print("print str",str)

    @wrapEmit
    def warning(self, msg, *args, **kwargs):
        """
        Delegate a warning call to the underlying logger.
        """
        super().warning( msg, *args, **kwargs)

    @wrapEmit
    def warn(self, msg, *args, **kwargs):
        # warnings.warn("The 'warn' method is deprecated, "
        #     "use 'warning' instead", DeprecationWarning, 2)
        # self.warning(msg, *args, **kwargs)
        super().warn( msg, *args, **kwargs)
    @wrapEmit
    def error(self, msg, *args, **kwargs):
        """
        Delegate an error call to the underlying logger.
        """
        super().error( msg, *args, **kwargs)
    @wrapEmit
    def exception(self, msg, *args, exc_info=True, **kwargs):
        """
        Delegate an exception call to the underlying logger.
        """
        super().exception( msg, *args, exc_info=exc_info, **kwargs)

        #super(mylogger,self).info(str)
    @wrapEmit
    def critical(self, msg, *args, **kwargs):
        """
        Delegate a critical call to the underlying logger.
        """
        super().critical( msg, *args, **kwargs)



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
