import bitstring
import collections
import heapq


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
            symbol = stream.read("uint:8")
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
    out = []
    try:
        while 1:
            out.append(tree.read(stream))
    except bitstring.ReadError:
        pass

    return bytes(out)
