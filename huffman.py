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

    def append_to_code(self, bit):
        for child in self.left, self.right:
            child.append_to_code(bit)

    def codes(self):
        out = self.left.codes()
        out.update(self.right.codes())
        return out

    def binary(self, out=None):
        out = bitstring.BitArray("0b0")
        out.append(self.left.binary())
        out.append(self.right.binary())
        return out

    @staticmethod
    def from_binary(data):
        stream = bitstring.BitStream(data)
        code = bitstring.BitArray()
        return Node._from_binary(stream, code)

    @staticmethod
    def _from_binary(stream, code):
        if stream.read("bool"):
            symbol = stream.read("bytes:1")
            return LeafNode(symbol, code=code)
        else:
            return Node(
                Node._from_binary(stream, bitstring.Bits("0b1") + code),
                Node._from_binary(stream, bitstring.Bits("0b0") + code))

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
            first.append_to_code(1)
            second.append_to_code(0)
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

    def append_to_code(self, bit):
        self.code.append("0b%s" % bit)

    def codes(self):
        return {self.symbol: self.code}

    def binary(self):
        out = bitstring.BitArray("0b1")
        out.append(bitstring.Bits(uint=self.symbol, length=8))
        return out


def compress(data, weights=None):
    """Performs huffman compression on data.
       data - The data to compress (iterable).
       weights - The weights for each code point. If None, we will use the
           number of occurances. Should be formatted as {symbol: weight}.

       returns (compressed_data, huffman_tree)
    """
    tree = Node.from_data(data, weights)
    codes = tree.codes()

    output = tree.binary()
    print(output)


def decompress(data):
    pass


class TestHuffmanCoding(unittest.TestCase):
    _simple = b"122333"
    _simple_codes = {
        "1": "11",
        "2": "01",
        "3": "0"
    }
    _simple_bits = bitstring.Bits("0b00100110001100110010100110011")

    _lorem = (b"Lorem ipsum dolor sit amet, consectetur adipisicing "
        b"elit, sed do eiusmod tempor incididunt ut labore et dolore magna "
        b"aliqua. Ut enim ad minim veniam, quis nostrud exercitation "
        b"ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis "
        b"aute irure dolor in reprehenderit in voluptate velit esse cillum "
        b"dolore eu fugiat nulla pariatur. Excepteur sint occaecat "
        b"cupidatat non proident, sunt in culpa qui officia deserunt "
        b"mollit anim id est laborum.")
    _lorem_codes = {
        " ": "100",
        ",": "0001001",
        ".": "111111",
        "D": "101101001",
        "E": "001101001",
        "L": "11011111",
        "U": "01011111",
        "a": "1110",
        "b": "0011111",
        "c": "10010",
        "d": "11000",
        "e": "0000",
        "f": "1011001",
        "g": "0011001",
        "h": "11101001",
        "i": "011",
        "l": "0111",
        "m": "00010",
        "n": "0101",
        "o": "0110",
        "p": "01111",
        "q": "111001",
        "r": "1101",
        "s": "01000",
        "t": "1010",
        "u": "0001",
        "v": "0101001",
        "x": "1001001"
    }
    _lorem_bits = bitstring.Bits("0x025c532ab62b85b2d25cadc2e2b359c5a144a2dd97"
        "8965d4586deba2c76d480b25cec, 0b101")

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
        tree = Node.from_binary(self._simple_bits)
        codes = {symbol.decode("UTF-8"): code.unpack("bin")[0]
                 for symbol, code in tree.codes().items()}
        self.assertEqual(codes, self._simple_codes)

        tree = Node.from_binary(self._lorem_bits)
        codes = {symbol.decode("UTF-8"): code.unpack("bin")[0]
                 for symbol, code in tree.codes().items()}
        self.assertEqual(codes, self._lorem_codes)

    def test_compression(self):
        #compressed = compress(self._simple)
        pass

if __name__ == "__main__":
    unittest.main()
