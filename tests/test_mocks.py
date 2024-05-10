class MockExecutor:
    @staticmethod
    def post_process(output):
        return output

    @staticmethod
    async def generate(_a, _b, _c, _d, _e):
        yield ("", {"tokens": 5, "token_type": "input"})
        yield ("You are an automated chicken", {"tokens": 1, "token_type": "output"})


class MockJsonParseFailureExecutor:
    @staticmethod
    def post_process(output):
        return output

    @staticmethod
    async def generate(_a, _b, _c, _d, _e):
        yield ('{"abc": "def"', {"tokens": 1, "token_type": "output"})


class MockJsonExecutor:
    @staticmethod
    def post_process(output):
        return output

    @staticmethod
    async def generate(_a, _b, _c, _d, _e):
        yield ('{"abc": "def"}', {"tokens": 1, "token_type": "output"})
