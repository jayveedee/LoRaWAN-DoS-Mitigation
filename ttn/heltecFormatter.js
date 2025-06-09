function decodeUplink(input) {
  const bytes = input.bytes;

  return {
    data: {
      text: String.fromCharCode(bytes[0], bytes[1], bytes[2], bytes[3]),
      count: bytes[4]
    }
  };
}