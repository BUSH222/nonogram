class Perlin2D:
    def __init__(self, seed):
        self.seed = seed
        self.gradients = [
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (-1, 1), (1, -1), (-1, -1)
        ]
        self.permutation = self._generate_permutation(seed)

    def _generate_permutation(self, seed):
        import random
        random.seed(seed)
        p = list(range(256))
        random.shuffle(p)
        return p + p

    def _hash(self, x, y):
        index = self.permutation[(self.permutation[x % 256] + y) % 256]
        return index % len(self.gradients)

    def _fade(self, t):
        return t * t * (3 - 2 * t)

    def _lerp(self, a, b, t):
        return a + (b - a) * t

    def _dot(self, gradient, dx, dy):
        return gradient[0] * dx + gradient[1] * dy

    def noise(self, x, y):
        xi = int(x) & 255
        yi = int(y) & 255

        xf = x - int(x)
        yf = y - int(y)

        u = self._fade(xf)
        v = self._fade(yf)

        g00 = self.gradients[self._hash(xi, yi)]
        g10 = self.gradients[self._hash(xi + 1, yi)]
        g01 = self.gradients[self._hash(xi, yi + 1)]
        g11 = self.gradients[self._hash(xi + 1, yi + 1)]

        n00 = self._dot(g00, xf, yf)
        n10 = self._dot(g10, xf - 1, yf)
        n01 = self._dot(g01, xf, yf - 1)
        n11 = self._dot(g11, xf - 1, yf - 1)

        nx0 = self._lerp(n00, n10, u)
        nx1 = self._lerp(n01, n11, u)
        result = self._lerp(nx0, nx1, v)

        return (result+1)/2
