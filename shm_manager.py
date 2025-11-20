from multiprocessing import shared_memory
import struct


class SharedMemoryManager:
    def __init__(self, name: str, size: int):
        self.name = name
        self.size = size
        self.shm = None

    def __enter__(self):
        self.shm = shared_memory.SharedMemory(
            name=self.name, create=True, size=self.size
        )
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            self.shm.close()
        finally:
            self.shm.unlink()

    def write_bytes(self, offset: int, data: bytes):
        end = offset + len(data)
        if end > self.size:
            raise ValueError("write exceeds shared memory size")
        self.shm.buf[offset:end] = data

    def read_bytes(self, offset: int, length: int) -> bytes:
        end = offset + length
        if end > self.size:
            raise ValueError("read exceeds shared memory size")
        return bytes(self.shm.buf[offset:end])

    def write_double(self, offset: int, value: float):
        self.write_bytes(offset, struct.pack("d", value))

    def read_double(self, offset: int) -> float:
        return struct.unpack("d", self.read_bytes(offset, 8))[0]
