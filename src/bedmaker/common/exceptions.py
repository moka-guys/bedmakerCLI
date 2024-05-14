class transcriptsException(Exception):
    pass


class MissingRefseqStableId(transcriptsException):
    pass


class InvalidTranscriptId(transcriptsException):
    pass
