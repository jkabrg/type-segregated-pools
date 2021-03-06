import random
from typing import TypeVar, Generic, Callable

T = TypeVar('T')
class Handle(Generic[T]):
    def __init__(self, index:int):
        self.index = index
        self.use_after_free_check = random.random()

class UseAfterFreeException(Exception):
    pass

class PoolOutOfSpaceException(Exception):
    pass

class Pool(Generic[T]):
    def __init__(self, size:int, constructor:Callable[[],T]=None):
        self.array = [None]*size
        self.free_slots = [Handle(index) for index in range(size)] # to make allocation O(1)
        self.use_after_free_checks = [None]*size
        self.constructor = constructor

    def check_for_use_after_free(self, handle:Handle[T]):
        if handle.use_after_free_check != self.use_after_free_checks[handle.index]:
            raise UseAfterFreeException()

    def __getitem__(self, handle:Handle[T])->T:
        self.check_for_use_after_free(handle)
        return self.array[handle.index]

    def alloc(self, constructor:Callable[[],T]=None) -> Handle:
        if constructor is None:
            constructor = self.constructor
        try:
            handle = self.free_slots.pop()
        except IndexError:
            raise PoolOutOfSpaceException()
        self.array[handle.index] = constructor()
        self.use_after_free_checks[handle.index] = handle.use_after_free_check
        return handle

    def free(self, handle:Handle[T]):
        self.check_for_use_after_free(handle)
        self.use_after_free_checks[handle.index] = None
        self.free_slots.append(Handle(handle.index))

class ScopedHandle(Generic[T]):
    def __init__(self, pool:Pool[T], *args):
        self.pool = pool
        self.handle = pool.alloc(*args)

    def __enter__(self):
        return self.handle

    def __exit__(self, type, value, traceback):
        #Exception handling here
        self.pool.free(self.handle)
        self.pool = None
        self.handle = None

if __name__ == '__main__':
    myPool = Pool[int](100, constructor=int)
    myHandle = myPool.alloc()
    print(myPool[myHandle])
    myPool.free(myHandle)

    floatPool = Pool[float](100)
    strPool = Pool[str](100)
    with ScopedHandle(floatPool, lambda: 1.0) as float_handle,\
         ScopedHandle(strPool, lambda: "blabla") as str_handle:
             print(floatPool[float_handle])
             print(strPool[str_handle])