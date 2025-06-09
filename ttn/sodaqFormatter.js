function decodeUplink(input) {
  let text = String.fromCharCode(...input.bytes.slice(0, 4));
  let count = Array.from(input.bytes.slice(4), byte => byte);

  return {
    data: {
      text: text,
      count: count
    }
  };
}