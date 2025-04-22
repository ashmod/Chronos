class Execution:
    def __init__(self, start_time: int, end_time: int):
        self.__start_time: int = start_time
        self.__end_time: int = end_time

    def duration(self) -> int:
        return self.__end_time - self.__start_time

    def get_start_time(self) -> int:
        return self.__start_time

    def set_start_time(self, start_time) -> None:
        self.__start_time = start_time

    def get_end_time(self) -> int:
        return self.__end_time

    def set_end_time(self, end_time) -> None:
        self.__end_time = end_time
