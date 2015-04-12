#!/usr/bin/env python3
import bitstring

from compression import huffman


simple = b"122333"
simple_codes = {
    "1": "11",
    "2": "10",
    "3": "0"
}
simple_tree = bitstring.Bits("0b00100110001100110010100110011")
simple_compressed = bitstring.Bits("0x498cca67d0")

lorem = (b"Lorem ipsum dolor sit amet, consectetur adipisicing "
    b"elit, sed do eiusmod tempor incididunt ut labore et dolore magna "
    b"aliqua. Ut enim ad minim veniam, quis nostrud exercitation "
    b"ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis "
    b"aute irure dolor in reprehenderit in voluptate velit esse cillum "
    b"dolore eu fugiat nulla pariatur. Excepteur sint occaecat "
    b"cupidatat non proident, sunt in culpa qui officia deserunt "
    b"mollit anim id est laborum.")
lorem_codes = {
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
lorem_tree = bitstring.Bits("0x025c532ab62b85b2d25cadc2e2b359c5a144a2dd97"
    "8965d4586deba2c76d480b25cec, 0b101")
lorem_compressed = bitstring.Bits("0x0204b8a6556c570b65a4b95b85c566b38b42"
    "8945bb2f12cba8b0dbd7458eda90164b9d97edac10778508236e6b22ca5d00b20a5a8"
    "4095058b2e3dec2c9d530876590440323621a04861950479acea4e1e1c529853cff1a"
    "c08291b7358143cca72fda787fcfd290ac82e328d59065056744833c611a612dc0c84"
    "90b4e575cd463b9d0963cff1af08d61630a5fb4f1bc42490729642186c52d4209e1d7"
    "f32d8c22f0a075c5811b7359d46c3d612e1430bca75194dd1e57503283b2901080a77"
    "74208db9ac08419b1333a9a8ee73e7bceb17f996494879422c8b52964a5c12ea531ec"
    "3757534d47d6d8614b208a294ea298ef399e3169b37273918082e294a1bbb297ac838"
    "6404a79fe35c23f")


def test_tree_from_data():
    tree = huffman.Node.from_data(simple)
    codes = {chr(symbol): code.unpack("bin")[0]
             for symbol, code in tree.codes().items()}
    assert(codes == simple_codes)

    tree = huffman.Node.from_data(lorem)
    codes = {chr(symbol): code.unpack("bin")[0]
             for symbol, code in tree.codes().items()}
    assert(codes == lorem_codes)

def test_tree_from_binary():
    tree = huffman.Node.from_binary(simple_tree)
    codes = {chr(symbol): code.unpack("bin")[0]
             for symbol, code in tree.codes().items()}
    assert(codes == simple_codes)

    tree = huffman.Node.from_binary(lorem_tree)
    codes = {chr(symbol): code.unpack("bin")[0]
             for symbol, code in tree.codes().items()}
    assert(codes == lorem_codes)

def test_compression():
    compressed = huffman.compress(simple)
    assert(bitstring.Bits(compressed) == simple_compressed)

    compressed = huffman.compress(lorem)
    assert(bitstring.Bits(compressed) == lorem_compressed)

def test_decompression():
    data = huffman.decompress(simple_compressed)
    assert(data == simple)

    data = huffman.decompress(lorem_compressed)
    assert(data == lorem)

def test_both():
    compressed = huffman.compress(simple)
    data = huffman.decompress(compressed)
    assert(data == simple)

    compressed = huffman.compress(lorem)
    data = huffman.decompress(compressed)
    assert(data == lorem)
