#!/usr/bin/env python3
import bitstring
import collections
import heapq
import unittest


class Node(object):
    def __init__(self, left, right):
        if left.weight is None:
            self.weight = None
        else:
            self.weight = left.weight + right.weight
        self.left = left
        self.right = right
        self.symbol = left.symbol

    def __lt__(self, other):
        # If weights are equal, sort based on symbol. We do this so that the
        # huffman tree will be deterministic, which makes it easier to test.
        if self.weight == other.weight:
            return self.symbol < other.symbol
        return self.weight < other.weight

    def add_to_code(self, bit):
        for child in self.left, self.right:
            child.add_to_code(bit)

    def codes(self):
        out = self.left.codes()
        out.update(self.right.codes())
        return out

    def read(self, stream):
        if stream.read("bool"):
            return self.left.read(stream)
        else:
            return self.right.read(stream)

    def binary(self, out=None):
        out = bitstring.BitArray("0b0")
        out.append(self.left.binary())
        out.append(self.right.binary())
        return out

    @staticmethod
    def from_binary(stream):
        try:
            stream.pos
        except AttributeError:
            stream = bitstring.BitStream(stream)
        code = bitstring.BitArray()
        out = Node._from_binary(stream, code)
        return out

    @staticmethod
    def _from_binary(stream, code):
        if stream.read("bool"):
            symbol = stream.read("bytes:1")
            return LeafNode(symbol, code=code)
        else:
            return Node(
                Node._from_binary(stream, code + bitstring.Bits("0b1")),
                Node._from_binary(stream, code + bitstring.Bits("0b0")))

    @staticmethod
    def from_data(data, weights=None):
        if weights is None:
            weights = collections.Counter(data)

        heap = []
        for symbol, weight in weights.items():
            heapq.heappush(heap, LeafNode(symbol, weight))

        while len(heap) > 1:
            first = heapq.heappop(heap)
            second = heapq.heappop(heap)
            first.add_to_code(1)
            second.add_to_code(0)
            heapq.heappush(heap, Node(first, second))

        return heap[0]


class LeafNode(Node):
    def __init__(self, symbol, weight=None, code=None):
        self.symbol = symbol
        self.weight = weight
        if code is not None:
            self.code = code
        else:
            self.code = bitstring.BitArray()

    def add_to_code(self, bit):
        self.code.prepend("0b%s" % bit)

    def codes(self):
        return {self.symbol: self.code}

    def binary(self):
        out = bitstring.BitArray("0b1")
        out.append(bitstring.Bits(uint=self.symbol, length=8))
        return out

    def read(self, stream):
        return self.symbol


def compress(data, weights=None):
    """Performs huffman compression on data.
       data - The data to compress (bytes).
       weights - The weights for each code point. If None, we will use the
           number of occurances. Should be a dict of {symbol: weight}.

       return - The compressed data, with the huffman tree prepended (bytes).
    """
    tree = Node.from_data(data, weights)
    codes = tree.codes()

    output = tree.binary()
    for byte in data:
        output.append(codes[byte])

    # Pad the front with 0's followed by 1 so we know where the real data
    # starts
    pad_bits = 8 - (len(output) % 8)
    if pad_bits == 0:
        pad_bits = 8

    padding = bitstring.BitArray()
    for i in range(pad_bits - 1):
        padding.append("0b0")
    padding.append("0b1")
    output.prepend(padding)

    return output.tobytes()


def decompress(data):
    """Decompresses huffman compressed data.
       data - The compressed data, with the huffman tree prepended (bytes).

       return - The decompressed data (bytes)
    """
    stream = bitstring.BitStream(data)

    # Read padding
    while not stream.read("bool"):
        pass

    tree = Node.from_binary(stream)
    out = b""
    try:
        while 1:
            out += tree.read(stream)
    except bitstring.ReadError:
        pass

    return out


class TestHuffmanCoding(unittest.TestCase):
    _simple = b"122333"
    _simple_codes = {
        "1": "11",
        "2": "10",
        "3": "0"
    }
    _simple_tree = bitstring.Bits("0b00100110001100110010100110011")
    _simple_compressed = bitstring.Bits("0x498cca67d0")

    _lorem = (b"Lorem ipsum dolor sit amet, consectetur adipisicing "
        b"elit, sed do eiusmod tempor incididunt ut labore et dolore magna "
        b"aliqua. Ut enim ad minim veniam, quis nostrud exercitation "
        b"ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis "
        b"aute irure dolor in reprehenderit in voluptate velit esse cillum "
        b"dolore eu fugiat nulla pariatur. Excepteur sint occaecat "
        b"cupidatat non proident, sunt in culpa qui officia deserunt "
        b"mollit anim id est laborum.")
    _lorem_codes = {
        " ": "001",
        ",": "1001000",
        ".": "111111",
        "D": "100101101",
        "E": "100101100",
        "L": "11111011",
        "U": "11111010",
        "a": "0111",
        "b": "1111100",
        "c": "01001",
        "d": "00011",
        "e": "0000",
        "f": "1001101",
        "g": "1001100",
        "h": "10010111",
        "i": "110",
        "l": "1110",
        "m": "01000",
        "n": "1010",
        "o": "0110",
        "p": "11110",
        "q": "100111",
        "r": "1011",
        "s": "00010",
        "t": "0101",
        "u": "1000",
        "v": "1001010",
        "x": "1001001"
    }
    _lorem_tree = bitstring.Bits("0x025c532ab62b85b2d25cadc2e2b359c5a144a2dd97"
        "8965d4586deba2c76d480b25cec, 0b101")
    _lorem_compressed = bitstring.Bits("0x0204b8a6556c570b65a4b95b85c566b38b42"
        "8945bb2f12cba8b0dbd7458eda90164b9d97edac10778508236e6b22ca5d00b20a5a8"
        "4095058b2e3dec2c9d530876590440323621a04861950479acea4e1e1c529853cff1a"
        "c08291b7358143cca72fda787fcfd290ac82e328d59065056744833c611a612dc0c84"
        "90b4e575cd463b9d0963cff1af08d61630a5fb4f1bc42490729642186c52d4209e1d7"
        "f32d8c22f0a075c5811b7359d46c3d612e1430bca75194dd1e57503283b2901080a77"
        "74208db9ac08419b1333a9a8ee73e7bceb17f996494879422c8b52964a5c12ea531ec"
        "3757534d47d6d8614b208a294ea298ef399e3169b37273918082e294a1bbb297ac838"
        "6404a79fe35c23f")

    def test_tree_from_data(self):
        tree = Node.from_data(self._simple)
        codes = {chr(symbol): code.unpack("bin")[0]
                 for symbol, code in tree.codes().items()}
        self.assertEqual(codes, self._simple_codes)

        tree = Node.from_data(self._lorem)
        codes = {chr(symbol): code.unpack("bin")[0]
                 for symbol, code in tree.codes().items()}
        self.assertEqual(codes, self._lorem_codes)

    def test_tree_from_binary(self):
        tree = Node.from_binary(self._simple_tree)
        codes = {symbol.decode("UTF-8"): code.unpack("bin")[0]
                 for symbol, code in tree.codes().items()}
        self.assertEqual(codes, self._simple_codes)

        tree = Node.from_binary(self._lorem_tree)
        codes = {symbol.decode("UTF-8"): code.unpack("bin")[0]
                 for symbol, code in tree.codes().items()}
        self.assertEqual(codes, self._lorem_codes)

    def test_compression(self):
        compressed = compress(self._simple)
        self.assertEqual(bitstring.Bits(compressed), self._simple_compressed)

        compressed = compress(self._lorem)
        self.assertEqual(bitstring.Bits(compressed), self._lorem_compressed)

    def test_decompression(self):
        data = decompress(self._simple_compressed)
        self.assertEqual(data, self._simple)

        data = decompress(self._lorem_compressed)
        self.assertEqual(data, self._lorem)

    def test_both(self):
        compressed = compress(self._simple)
        data = decompress(compressed)
        self.assertEqual(data, self._simple)

        compressed = compress(self._lorem)
        data = decompress(compressed)
        self.assertEqual(data, self._lorem)


if __name__ == "__main__":
    unittest.main()
