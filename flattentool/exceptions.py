class FlattenToolWarning(UserWarning):
    """
    A warning generated directly by flatten-tool.

    """

    pass


class DataErrorWarning(FlattenToolWarning):
    """
    A warnings that indicates an error in the data, rather than the schema.

    """

    pass
