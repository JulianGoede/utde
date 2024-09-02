class CheckError(Exception):
    pass


class TypeCheckError(CheckError):
    pass


class LintCheckError(CheckError):
    pass
