# CPU

## Austro Architecture

The simulated Austro CPU is on purpose, for educational reasons, based on Intel 8086. It has the following characteristics.

### 16 bits

Austro CPU work with a [memory word]{target=_blank} of 16 bits (2 bytes). This means for the CPU some things:

- The registers, the internal memory of the CPU, must have (each) 16 bits as well.
- The largest block that can be transferred to and from the memory is of 16 bits.
- The maximum RAM the computer can work is 2^16^ bytes, which is 64 KB.

[memory word]: https://en.wikipedia.org/wiki/Word_(computer_architecture)

/// note | You must be kidding!!!
Nowadays when we can found 64-bit processors even on a cell phone, defining a 16-bit one sounds like a waste of time.

You would probably be right, if it was a real CPU 😏
///

### Instruction Word



![Austro CPU Block Diagram](img/cpu-diagram.svg)

## Operations

--8<-- "assembly-ref.html"

## Registers

TBD
