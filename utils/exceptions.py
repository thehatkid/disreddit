class CannotSendMessages(Exception):
    """Raised when the bot can't send messages in given channel."""

    def __init__(self):
        pass

    def __str__(self):
        return 'Bot don\'t have permission to Send Messages to channel'


class SubredditNotFound(Exception):
    """Raised when the bot can't find subreddit or subreddit is private only with given display name."""

    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return 'Subreddit "{0}" was not found by given name'.format(self.name)


class SubredditIsPrivate(Exception):
    """Raised when the subreddit is private to access."""

    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return 'Subreddit "{0}" is private only by given name'.format(self.name)


class SubredditIsNSFW(Exception):
    """Raised when the subreddit is NSFW which channel is not NSFW marked."""

    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return 'Subreddit "{0}" is NSFW (over 18) but Channel is not NSFW marked'.format(self.name)
