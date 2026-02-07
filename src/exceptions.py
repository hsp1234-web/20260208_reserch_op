class TaifexError(Exception):
    pass

class TimeoutError(TaifexError):
    pass

class DownloaderError(TaifexError):
    pass

class ConverterError(TaifexError):
    pass
