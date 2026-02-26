"""
HybridLink Boost Protocol (HFXC): 
Native Python implementation of the high-performance multipath protocol from HybridFileXfer.
"""

import struct
import io
import asyncio
import os
from dataclasses import dataclass
from typing import List, Optional

# Protocol Identifiers
@dataclass
class TransferIdentifiers:
    END_POINT = -1
    FILE = 0
    FOLDER = 1
    FILE_SLICE = 2
    EOF = 3
    END_OF_INTERRUPTED = 4
    END_OF_READ_ERROR = 5
    END_OF_WRITE_ERROR = 6

class MultiPathProtocol:
    """Handles the binary HFXC protocol for high-performance transfers."""
    
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer

    async def write_short(self, val: int):
        self.writer.write(struct.pack('>h', val))

    async def write_int(self, val: int):
        self.writer.write(struct.pack('>i', val))

    async def write_long(self, val: int):
        self.writer.write(struct.pack('>q', val))

    async def write_utf(self, val: str):
        utf_bytes = val.encode('utf-8')
        # Protocol uses Java DataOutputStream writeUTF: 2 bytes length + content
        self.writer.write(struct.pack('>H', len(utf_bytes)))
        self.writer.write(utf_bytes)

    async def read_short(self) -> int:
        return struct.unpack('>h', await self.reader.readexactly(2))[0]

    async def read_int(self) -> int:
        return struct.unpack('>i', await self.reader.readexactly(4))[0]

    async def read_long(self) -> int:
        return struct.unpack('>q', await self.reader.readexactly(8))[0]

    async def read_utf(self) -> str:
        length = struct.unpack('>H', await self.reader.readexactly(2))[0]
        return (await self.reader.readexactly(length)).decode('utf-8')

    async def send_file_block(self, file_index: int, path: str, last_modified: int, 
                             total_size: int, chunk_index: int, data: bytes):
        """Send a single high-speed file block."""
        await self.write_short(TransferIdentifiers.FILE)
        await self.write_int(file_index)
        await self.write_utf(path)
        await self.write_long(last_modified)
        await self.write_long(total_size)
        await self.write_int(chunk_index)
        await self.write_int(len(data))
        self.writer.write(data)
        await self.writer.drain()

    async def receive_block(self):
        """Receive a block from the network."""
        identifier = await self.read_short()
        if identifier == TransferIdentifiers.EOF:
            return None, None
        
        file_index = await self.read_int()
        path = await self.read_utf()
        last_modified = await self.read_long()
        
        if identifier == TransferIdentifiers.FOLDER:
            return "FOLDER", {"path": path, "last_modified": last_modified}
        
        total_size = await self.read_long()
        chunk_index = await self.read_int()
        data_len = await self.read_int()
        data = await self.reader.readexactly(data_len)
        
        return "FILE", {
            "file_index": file_index,
            "path": path,
            "last_modified": last_modified,
            "total_size": total_size,
            "chunk_index": chunk_index,
            "data": data
        }
